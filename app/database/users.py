'''
manages user accounts
'''

from datetime import datetime, timedelta
import hashlib
import ipaddress
import psycopg
import re
import secrets

from app.database.connectionPool import FdbConnection
from app.database.helpers import \
    FdbException, \
    currentTimeUtc
from app.database.logging import \
    logDatabaseInfoMessage, \
    logDatabaseWarnMessage

from app.config import \
    SESSION_LEN_DAYS, \
    DEBUG_EXTRA, \
    PWD_HASH_ITERS, \
    MIN_PWD_LEN

_USERNAME_RE = re.compile(r'\w+')
_EMAIL_RE = re.compile(r'[\w\-\.]+@[\w\-]+(\.[\w\-]+)+')
_SESS_LEN = timedelta(days=SESSION_LEN_DAYS)

class UserRow:
    '''
    object representation for row in users table
    TODO document table columns
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 12
            assert isinstance(row[0],int)
            assert row[1] is None or isinstance(row[1],str)
            assert row[2] is None or isinstance(row[2],str)
            assert row[3] is None or isinstance(row[3],str)
            assert isinstance(row[4],bytes)
            assert isinstance(row[5],bytes)
            assert isinstance(row[6],datetime)
            assert isinstance(row[7],datetime)
            assert row[8] is None or isinstance(row[8],datetime)
            assert isinstance(row[9],bool)
            assert isinstance(row[10],bool)
            assert row[11] is None or isinstance(row[11],bytes)
        self.id: int = row[0]
        self.username: str|None = row[1]
        self.email: str|None = row[2]
        self.fullname: str|None = row[3]
        self.pwd_hash: bytes = row[4]
        self.pwd_salt: bytes = row[5]
        self.created: datetime = row[6]
        self.modified: datetime = row[7]
        self.last_login: datetime|None = row[8]
        self.is_disabled: bool = row[9]
        self.is_admin: bool = row[10]
        self.api_key: bytes|None = row[11]

    def __repr__(self) -> str:
        return f'<UserRow(' \
            f'id={self.id},' \
            f'username={repr(self.username)},' \
            f'email{repr(self.email)},' \
            f'fullname={repr(self.fullname)},' \
            f'pwd_hash={repr(self.pwd_hash)},' \
            f'pwd_salt={repr(self.pwd_salt)},' \
            f'created={repr(self.created)},' \
            f'modified={repr(self.modified)},' \
            f'last_login={repr(self.last_login)},' \
            f'is_disabled={self.is_disabled},' \
            f'is_admin={self.is_admin})>'

class SessionRow:
    '''
    object representation for row in sessions table
    TODO document table columns
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 6
            assert isinstance(row[0],int)
            assert isinstance(row[1],bytes)
            assert isinstance(row[2],datetime)
            assert isinstance(row[3],datetime)
            assert isinstance(row[4],datetime)
            assert row[5] is None or isinstance(row[5],ipaddress.IPv4Address)
        self.user_id: int = row[0]
        self.token_hash: bytes = row[1]
        self.created: datetime = row[2]
        self.expires: datetime = row[3]
        self.accessed: datetime = row[4]
        self.last_ip: str = str(row[5])

    def __repr__(self) -> str:
        return f'<SessionRow(' \
            f'user_id={self.user_id},' \
            f'token_hash={repr(self.token_hash)},' \
            f'created={repr(self.created)},' \
            f'expires={repr(self.expires)},' \
            f'accessed={repr(self.accessed)},' \
            f'last_ip={repr(self.last_ip)})>'

def _generateToken() -> bytes:
    # 512 bit secure random token
    return secrets.token_bytes(64)

def _hashBytes(b:bytes,/) -> bytes:
    # sha512 hash
    return hashlib.sha512(b).digest()

def _hmac(k:bytes,m:bytes,/) -> bytes:
    # hash based message authentication code
    # see wikipedia article for details
    # using sha512 (128 byte block, 64 byte hash)
    if len(k) > 128: # longer keys are hashed first
        kp = _hashBytes(k)
    # shorter keys are zero padded to block size
    kp = k + b'\x00'*(128-len(k))
    x = bytes(byte ^ 0x5c for byte in kp) # k' ^ opad
    y = bytes(byte ^ 0x36 for byte in kp) # k' ^ ipad
    return _hashBytes(x + _hashBytes(y + m))

def _pbkdf2(pwd:bytes,salt:bytes,iters:int,/) -> bytes:
    # password based key derivation function
    # see wikipedia article for details (silghtly modified)
    assert iters > 0
    u = _hmac(pwd,salt)
    f = u
    for _ in range(iters-1):
        u = _hmac(pwd,u)
        f = bytes(f[i] ^ u[i] for i in range(64))
    return f

def _hashToken(tkn:bytes,/) -> bytes:
    # double sha512 to hash tokens
    return _hashBytes(_hashBytes(tkn))

def _hashPassword(pwd:str,salt:bytes,/) -> bytes:
    # pbkdf2 to hash passwords (several iterations to be slightly slow)
    return _pbkdf2(pwd.encode(),salt,PWD_HASH_ITERS)

def createUser(username:str,email:str,pwd:str,fullname:str):
    '''
    create a user account, username and email must be unique
    '''
    if len(username) > 32:
        raise FdbException('username is too long')
    if len(email) > 64:
        raise FdbException('email is too long')
    if len(fullname) > 64:
        raise FdbException('fullname is too long')
    if not _USERNAME_RE.fullmatch(username):
        raise FdbException('username contains invalid characters')
    if not _EMAIL_RE.fullmatch(email):
        raise FdbException('email format is incorrect')

    pwd_salt = _generateToken()
    pwd_hash = _hashPassword(pwd,pwd_salt)

    with FdbConnection() as con:
        con.execute("insert into users (username,fullname,email,"
                    "pwd_hash,pwd_salt) values (%s,%s,%s,%s,%s);",
                    (username,fullname,email,pwd_hash,pwd_salt))
        con.commit()
        logDatabaseInfoMessage(f'created user {username} with email {email}')

def _getUser(u:int|str,con:psycopg.Connection,/) -> None|UserRow:
    if isinstance(u,int):
        cur = con.execute("select * from users where id = %s;",(u,))
        row = cur.fetchone()
        return None if row is None else UserRow(row)
    else:
        cur = con.execute("select * from users where username = %s;",(u,))
        row = cur.fetchone()
        if row is not None:
            return UserRow(row)
        cur = con.execute("select * from users where email = %s;",(u,))
        row = cur.fetchone()
        return None if row is None else UserRow(row)

def getUser(user:str|int,/) -> None|UserRow:
    '''
    get user details from id, username, or email
    '''
    with FdbConnection() as con:
        return _getUser(user,con)

def verifyUser(user:str|int,pwd:str,ip:str|None) -> None|UserRow:
    '''
    check user login both by id/username/email, none if invalid login
    '''
    # log some info to identify attempts of unauthorized access
    with FdbConnection() as con:
        row = _getUser(user,con)
        if row is None:
            logDatabaseWarnMessage(f'login attempt from {ip} (invalid user)')
            return None

        h = _hashPassword(pwd,row.pwd_salt)
        valid = secrets.compare_digest(h,row.pwd_hash)
        if valid:
            logDatabaseWarnMessage(f'verified login for {user} from {ip}')
            return row
        else:
            logDatabaseWarnMessage(f'login attempt from {ip} '
                                   f'(invalid password for {user})')
            return None

def changeUserPassword(user:str|int,new:str,old:str|None):
    '''
    change a password (to new), if old is not none then check it first
    exception if user does not exist or incorrect password
    '''
    with FdbConnection() as con:
        row = _getUser(user,con)
        if row is None:
            raise FdbException('user does not exist')

        if len(new) < MIN_PWD_LEN:
            raise FdbException('minimum password length is '
                               f'{MIN_PWD_LEN} characters')

        if len(new) > 128:
            raise FdbException('maximum password length is 128 characters')

        if isinstance(old,str): # check old password first
            h = _hashPassword(old,row.pwd_salt)
            valid = secrets.compare_digest(h,row.pwd_hash)
            if not valid:
                raise FdbException('old password is incorrect')

        newsalt = _generateToken()
        newhash = _hashPassword(new,newsalt)

        con.execute("update users set pwd_hash = %s, pwd_salt = %s, "
                    "modified = default where id = %s;",
                    (newhash,newsalt,row.id))
        con.commit()
        logDatabaseWarnMessage(f'changed password for user {row.username}')

def setUserDisabled(user:str,b:bool,/):
    '''
    set the disabled status of an account
    '''
    with FdbConnection() as con:
        row = _getUser(user,con)
        if row is None:
            raise FdbException('user does not exist')
        con.execute("update users set is_disabled = %s, modified = default "
                    "where id = %s;",(b,row.id))
        if b:
            con.execute("delete from sessions where user_id = %s;",(row.id,))
        con.commit()
        logDatabaseInfoMessage(
            f'set user {user} as {'disabled' if b else 'enabled'}')

def setUserAdmin(user:str,b:bool,/):
    '''
    set the admin status of an account
    '''
    with FdbConnection() as con:
        row = _getUser(user,con)
        if row is None:
            raise FdbException('user does not exist')
        con.execute("update users set is_admin = %s, modified = default "
                    "where id = %s;",(b,row.id))
        con.commit()
        logDatabaseInfoMessage(
            f'set user {user} as {'admin' if b else 'not admin'}')

def _getSession(th:bytes,con:psycopg.Connection,/) -> None|SessionRow:
    # th = token hash
    cur = con.execute("select * from sessions where token_hash = %s;",(th,))
    row = cur.fetchone()
    return None if row is None else SessionRow(row)

def _deleteSession(th:bytes,con:psycopg.Connection,/):
    # th = token hash
    con.execute("delete from sessions where token_hash = %s;",(th,))
    con.commit()

def getSession(token:bytes) -> None|SessionRow:
    '''
    get a session row if it exists and is not expired,
    if update then user/session timestamp details are modified
    '''
    with FdbConnection() as con:
        token_hash = _hashToken(token)
        row = _getSession(token_hash,con)
        if row is None:
            return None
        if currentTimeUtc() < row.expires:
            return row
        else:
            _deleteSession(token_hash,con)
            return None

def updateSession(token:bytes,ip:str|None) -> datetime:
    '''
    update session expiration time, returns new expiration timestamp
    '''
    with FdbConnection() as con:
        token_hash = _hashToken(token)
        exp = currentTimeUtc() + _SESS_LEN
        con.execute("update sessions set accessed = default, last_ip = %s, "
                    "expires = %s where token_hash = %s;",
                    (ip,exp,token_hash))
        con.commit()
        return exp

def createSession(user:str,ip:str|None) -> str:
    '''
    create a login session for a user, returns the token for the cookie
    '''
    expires = currentTimeUtc() + _SESS_LEN
    token = _generateToken()
    token_hash = _hashToken(token)
    with FdbConnection() as con:
        row = _getUser(user,con)
        if row is None:
            raise FdbException('user does not exist')
        con.execute("insert into sessions (user_id,token_hash,expires,last_ip)"
                    "values (%s,%s,%s,%s);",
                    (row.id,token_hash,expires,ip))
        con.execute("update users set last_login = default where id = %s;",
                    (row.id,))
        con.commit()
        logDatabaseInfoMessage(
            f'created session for user {user} with token hash '
            f'{token_hash.hex()[:10]}..')
        return token.hex()

def deleteSession(token:bytes):
    '''
    delete a login session
    '''
    h = _hashToken(token)
    with FdbConnection() as con:
        cur = con.execute("delete from sessions where token_hash = %s "
                          "returning user_id;",(h,))
        row = cur.fetchone()
        if row is None:
            return
        con.commit()
        logDatabaseInfoMessage(f'deleted session for user id {row[0]} '
                               f'with token hash {h.hex()[:10]}..')

def deleteUser(user:str):
    '''
    delete a user account
    '''
    with FdbConnection() as con:
        row = _getUser(user,con)
        if row is None:
            raise FdbException('user does not exist')
        con.execute("update users set username = null, email = null, "
                    "fullname = '', modified = default where id = %s;",
                    (row.id,))
        con.execute("delete from sessions where user_id = %s;",(row.id,))
        con.commit()
        logDatabaseInfoMessage(f'deleted user id {row.id}')

def makeApiKey(user:str|int) -> bytes:
    '''
    generate a new API key for the user
    '''
    key = _generateToken()
    with FdbConnection() as con:
        user_row = getUser(user)
        if user_row is None:
            raise FdbException('user does not exist')
        con.execute("update users set api_key = %s where id = %s;",
                    (_hashToken(key),user_row.id))
    return key

def findApiKey(key:bytes) -> None|UserRow:
    '''
    lookup the user associated with an API key
    '''
    with FdbConnection() as con:
        cur = con.execute("select * from users where api_key = %s;",
                          (_hashToken(key),))
        row = cur.fetchone()
        return None if row is None else UserRow(row)
