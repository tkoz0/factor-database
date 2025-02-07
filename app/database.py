from datetime import datetime, timedelta, UTC
import hashlib
import ipaddress
import os
import re
import requests
import secrets
import struct
import sys
import time
from typing import Generator,Iterable

import psycopg
import psycopg.sql

from app.config import \
    PWD_HASH_ITERS, SESSION_LEN_DAYS, MIN_PWD_LEN, \
    NUM_BIT_LIM, PRP_BIT_LIM, PROVE_BIT_LIM, \
    LOG_TO_FILE, DEBUG_EXTRA, DB_CON_LIM, \
    DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

from app.maths import prpTest, primeTest

scriptdir = os.path.dirname(__file__)

# comments ===========================================================

'''
factor database
- for accessing and modifying an existing factor database
- provides an interface for performing desired operations
- database setup must be completed first, see setup_postgres.sql
'''

'''
old sqlite3 stuff
_con = sqlite3.connect('database.sqlite3')
_con.create_function('regexp',2,_regexp)
_con.execute('pragma foreign_keys = on;')
_cur = _con.cursor()
'''

#===============================================================================
# constants
#===============================================================================

class Primality:
    ''' primality constants '''
    UNKNOWN = -1
    COMPOSITE = 0
    PROBABLE = 1
    PRIME = 2

class LogLevel:
    ''' logging level types '''
    INFO = 0
    WARN = 1
    CRIT = 2

_time_fmt = '%Y-%m-%d %H:%M:%S'

_con_str = f'postgres://{DB_USER}@{DB_HOST}/{DB_NAME}' if DB_PORT == 5432 \
      else f'postgres://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

_path_name_re = re.compile(r'[\w\+\-\=][\w\+\-\=\.]*')

_username_re = re.compile(r'\w+')

#_email_re = re.compile(r'[^@]+@[^@]+')
_email_re = re.compile(r'[\w\-\.]+@[\w\-]+(\.[\w\-]+)+')

_sess_len = timedelta(days=SESSION_LEN_DAYS)

_endpoint_factordb = 'https://factordb.com/api'

#===============================================================================
# helper functions
#===============================================================================

def _now() -> datetime:
    ''' current utc time '''
    # note: sqlite3 does not have date type
    # (convert to .timestamp() which is unix float if supporting sqlite3)
    return datetime.now(UTC).replace(tzinfo=None)

def _ts_to_str(d:datetime) -> str:
    ''' convert timestamp to string format used by sqlite3 '''
    return time.strftime(_time_fmt,d.timetuple())

def _str_to_ts(s:str) -> datetime:
    ''' convert string (YYYY-mm-dd HH:MM:SS) to datetime object '''
    st = time.strptime(s,_time_fmt)
    return datetime.fromtimestamp(time.mktime(st)).replace(tzinfo=UTC)

def _regexp(expr:str, item:str) -> bool:
    ''' leftover function attempting to support sqlite3 regexp extension '''
    return re.search(expr,item) is not None

class FDBException(Exception):
    ''' exception type for database issues '''

#===============================================================================
# database connection pool
#===============================================================================

def _make_con() -> psycopg.Connection:
    #return psycopg.connect(host=DB_HOST,port=DB_PORT,
    #                       user=DB_USER,password=DB_PASS,dbname=DB_NAME)
    return psycopg.connect(_con_str,password=DB_PASS)

# reusable connection objects for any purpose
_con_pool: list[psycopg.Connection] = []
_con_count: int = 0

class _dbcon:
    '''
    for handling database connection
    with _fdbcon() as con: ...
    caller must call con.commit() if doing write operations
    '''

    def __init__(self):
        self.con = None

    def __enter__(self) -> psycopg.Connection:
        global _con_pool, _con_count
        if _con_pool == []:
            if _con_count >= DB_CON_LIM:
                _stderr_log(f'tried to open more than {DB_CON_LIM} connections')
                raise FDBException('exceeded database connection limit')
            self.con = _make_con()
            _con_count += 1
            _stderr_log(f'created connection, total is now {_con_count}')
        else:
            self.con = _con_pool.pop()
        return self.con

    def __exit__(self,exctyp,excval,traceback) -> None:
        #if exctyp is not None or excval is not None or traceback is not None:
        #    _stderr_log(f'_dbcon.__exit__ received {exctyp}: {excval}')
        #    _stderr_write(str(traceback))
        global _con_pool
        assert isinstance(self.con,psycopg.Connection)
        self.con.rollback()
        _con_pool.append(self.con)

def closeDatabaseConnections():
    global _con_pool, _con_count
    for con in _con_pool:
        con.close()
    _con_pool = []
    _con_count = 0

#===============================================================================
# logging
#===============================================================================

_logdir = f'{scriptdir}/../logs'
_logfile = None
if LOG_TO_FILE:
    os.makedirs(_logdir,exist_ok=True)
    name = time.strftime('%Y-%m-%d_%H-%M-%S',_now().timetuple())
    _logname = f'{_logdir}/{name}.log'
    _logfile = open(_logname,'a')

def _stderr_write(s:str):
    ''' write to stderr '''
    print(s,file=sys.stderr,flush=True)

def _stderr_log(s:str):
    ''' write a log message to stderr '''
    _stderr_write(f'[{__name__}] [{_ts_to_str(_now())}] {s}')

def _dblog_str(s:str,save_to_db:bool,level:int):
    ''' write message to stderr, database table, and possibly a log file '''
    global _logfile
    _stderr_log(s)
    if _logfile is not None:
        print(f'[{_ts_to_str(_now())}] {s}',file=_logfile,flush=True)
    if not save_to_db:
        return
    with _dbcon() as con:
        con.execute("insert into logs (text,level) values (%s,%s);",(s,level))
        con.commit()

def _dblog_debug(s:str):
    ''' log debug message (not saved in database) '''
    _dblog_str(f'[DEBUG] {s}',False,LogLevel.INFO)

def _dblog_info(s:str):
    ''' log database info message '''
    _dblog_str(f'[INFO] {s}',True,LogLevel.INFO)

def _dblog_warn(s:str):
    ''' log database warning message '''
    _dblog_str(f'[WARN] {s}',True,LogLevel.WARN)

def _dblog_crit(s:str):
    ''' log database critical message '''
    _dblog_str(f'[CRIT] {s}',True,LogLevel.CRIT)

def closeLogging():
    global _logfile,_logname
    if _logfile is not None:
        _logfile.close()
        if os.path.getsize(_logname) == 0:
            os.remove(_logname)

#===============================================================================
# data processing
#===============================================================================

def _int_to_dbnum(n:int) -> bytes:
    ''' convert nonnegative integer for database storage (to byte array) '''
    return n.to_bytes((n.bit_length()+7)//8,'big',signed=False)

def _dbnum_to_int(b:bytes) -> int:
    ''' convert database storage to integer (from byte array) '''
    return int.from_bytes(b,'big',signed=False)

def _spfs_to_dblists(ns:Iterable[int]) \
                    -> tuple[bytes|None,bytes|None,bytes|None]:
    '''
    convert small prime factors to byte arrays (big endian) for database
    all numbers must be prime, this function sorts them
    returns 3 byte arrays for 16/32/64 bit primes respectively
    '''
    ns = sorted(ns)
    n2 = [n for n in ns if n < 2**16]
    n4 = [n for n in ns if 2**16 <= n < 2**32]
    n8 = [n for n in ns if 2**32 <= n < 2**64]
    if DEBUG_EXTRA:
        assert len(n2) + len(n4) + len(n8) == len(ns)
        assert all(2 <= n <= 65521 for n in n2)
        assert all(65537 <= n <= 2**32 - 5 for n in n4)
        assert all(2**32 + 15 <= n <= 2**64 - 59 for n in n8)
        assert n2 == sorted(n2)
        assert n4 == sorted(n4)
        assert n8 == sorted(n8)
        assert all(primeTest(n) for n in ns)
    return struct.pack(f'>{len(n2)}H',*n2) if len(n2) else None, \
           struct.pack(f'>{len(n4)}I',*n4) if len(n4) else None, \
           struct.pack(f'>{len(n8)}Q',*n8) if len(n8) else None

def _dblists_to_spfs(b2:bytes|None,b4:bytes|None,b8:bytes|None) \
        -> tuple[tuple[int,...],tuple[int,...],tuple[int,...]]:
    '''
    extract small prime factors from database storage
    they will be prime and sorted
    '''
    return () if b2 is None else struct.unpack(f'>{len(b2)//2}H',b2), \
           () if b4 is None else struct.unpack(f'>{len(b4)//4}I',b4), \
           () if b8 is None else struct.unpack(f'>{len(b8)//8}Q',b8)

def _dbprp(n:int) -> int:
    # internal basic primality tester, must be fast
    # assumes n was already tested for small prime divisors
    if n.bit_length() > PRP_BIT_LIM:
        return Primality.UNKNOWN
    if n.bit_length() <= PROVE_BIT_LIM:
        return Primality.PRIME if primeTest(n) else Primality.COMPOSITE
    return Primality.PROBABLE if prpTest(n) else Primality.COMPOSITE

#===============================================================================
# factorization data
#===============================================================================

'''
number = a number > 1 whose factors are desired, can include primes
(desired examples: fibonacci numbers, repunit, cunningham numbers, ...)
factor = intermediate factoring results, can be the starting number
(small prime factors should be excluded by factoring before adding numbers)

factors maintain a primality status (unknown, composite, probable, prime)
when factored, they reference factorization f1*f2 where f1 <= f2
if multiple factorizations are found, store the best one (smallest f1)

numbers store small prime factors as part of the row storage
for production, try to find all 64 bit factors before inserting
for remaining large factors, reference a number in the factors table
numbers are marked as complete when the full prime factorization is known
'''

class FactorRow:
    '''
    object representation for row in factors table
    (row in "select * from factors")
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 7
            assert isinstance(row[0],int)
            assert isinstance(row[1],bytes)
            assert isinstance(row[2],int)
            assert row[3] is None or isinstance(row[3],int)
            assert row[4] is None or isinstance(row[4],int)
            assert isinstance(row[5],datetime)
            assert isinstance(row[6],datetime)
        self.id: int = row[0]
        self.value: int = _dbnum_to_int(row[1])
        self.primality: int = row[2]
        self.f1_id: int|None = row[3]
        self.f2_id: int|None = row[4]
        self.created: datetime = row[5]
        self.modified: datetime = row[6]

    def __repr__(self) -> str:
        return f'<FactorRow(id={self.id},' \
            f'value={self.value},' \
            f'primality={self.primality},' \
            f'f1_id={self.f1_id},' \
            f'f2_id={self.f2_id},' \
            f'created={repr(self.created)},' \
            f'modified={self.modified})>'

class NumberRow:
    '''
    object representation for row in numbers table
    (row in "select * from numbers")
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 9
            assert isinstance(row[0],int)
            assert isinstance(row[1],bytes)
            assert row[2] is None or isinstance(row[2],bytes)
            assert row[3] is None or isinstance(row[3],bytes)
            assert row[4] is None or isinstance(row[4],bytes)
            assert row[5] is None or isinstance(row[5],int)
            assert isinstance(row[6],bool)
            assert isinstance(row[7],datetime)
            assert isinstance(row[8],datetime)
        self.id: int = row[0]
        self.value: int = _dbnum_to_int(row[1])
        n2,n4,n8 = _dblists_to_spfs(row[2],row[3],row[4])
        if DEBUG_EXTRA:
            assert sorted(n2) == list(n2)
            assert sorted(n4) == list(n4)
            assert sorted(n8) == list(n8)
            assert all(2 <= n <= 65521 for n in n2)
            assert all(65537 <= n <= 2**32 - 5 for n in n4)
            assert all(2**32 + 15 <= n <= 2**64 - 59 for n in n8)
        self.spfs = n2 + n4 + n8
        self.cof_id: int|None = row[5]
        self.complete: bool = row[6]
        self.created: datetime = row[7]
        self.modified: datetime = row[8]

    def __repr__(self) -> str:
        return f'<NumberRow(' \
            f'id={self.id},' \
            f'value={self.value},' \
            f'spfs=[{','.join(map(str,self.spfs))}],' \
            f'cof_id={self.cof_id},' \
            f'complete={self.complete},' \
            f'created={repr(self.created)},' \
            f'modified={repr(self.modified)})>'

def _getnumv(n:int,con:psycopg.Connection) -> None|NumberRow:
    # get number by value (from connection)
    cur = con.execute("select * from numbers where value = %s;",
                      (_int_to_dbnum(n),))
    row = cur.fetchone()
    return None if row is None else NumberRow(row)

def getNumberByValue(n:int) -> None|NumberRow:
    '''
    returns the database row for a number (those to be factored)
    result is none if number is not in database
    '''
    if n < 2:
        return None
    with _dbcon() as con:
        return _getnumv(n,con)

def _getnumi(i:int,con:psycopg.Connection) -> None|NumberRow:
    # get number by id (from connection)
    cur = con.execute("select * from numbers where id = %s;",(i,))
    row = cur.fetchone()
    return None if row is None else NumberRow(row)

def getNumberByID(i:int) -> None|NumberRow:
    '''
    returns the database row for a number (those to be factored)
    result is none if number is not in database
    '''
    with _dbcon() as con:
        return _getnumi(i,con)

def _getfacv(n:int,con:psycopg.Connection) -> None|FactorRow:
    # get factor by value (from connection)
    cur = con.execute("select * from factors where value = %s;",
                      (_int_to_dbnum(n),))
    row = cur.fetchone()
    return None if row is None else FactorRow(row)

def getFactorByValue(n:int) -> None|FactorRow:
    '''
    returns the database row for a factor (intermediate results)
    result is none if factor is not in database
    '''
    if n <= 0:
        return None
    with _dbcon() as con:
        return _getfacv(n,con)

def _getfaci(i:int,con:psycopg.Connection) -> None|FactorRow:
    # get factor by id (from connection)
    cur = con.execute("select * from factors where id = %s;",(i,))
    row = cur.fetchone()
    return None if row is None else FactorRow(row)

def getFactorByID(i:int) -> None|FactorRow:
    '''
    returns the database row for a factor (intermediate results)
    result is none if factor is not in database
    '''
    with _dbcon() as con:
        return _getfaci(i,con)

def _getnums_withfac(ret:list[NumberRow],row:FactorRow,con:psycopg.Connection):
    # get numbers with factor i as a factor (primary factorization only)
    cur = con.execute("select * from numbers where cof_id = %s;",(row.id,))
    for nrow in cur.fetchall():
        ret.append(NumberRow(nrow))

    # numbers with current in its primary factorization
    cur = con.execute("select * from factors where f1_id = %s or f2_id = %s;",
                      (row.id,row.id))
    for frow in cur.fetchall():
        _getnums_withfac(ret,FactorRow(frow),con)

    # numbers with current in a secondary factorization
    cur = con.execute("select factors.* from factors_old "
                      "join factors on factors_old.fac_id = factors.id "
                      "where factors_old.f1_id = %s or factors_old.f2_id = %s;",
                      (row.id,row.id))
    for frow in cur.fetchall():
        _getnums_withfac(ret,FactorRow(frow),con)

def setFactorPrime(i:int, test:bool):
    '''
    sets a factor (by ID) as proven prime
    exception if an error occurs
    test = run prp test to check against
    '''
    with _dbcon() as con:
        row = _getfaci(i,con)
        if row is None:
            raise FDBException(f'factor id {i} does not exist in database')
        if row.value.bit_length() <= PROVE_BIT_LIM:
            raise FDBException(f'factor is small enough for primality proving')

        if test and not prpTest(row.value):
            raise FDBException(f'factor id {i} is actually composite')
        con.execute("update factors set primality = %s, "
                    "modified = default where id = %s;",
                    (Primality.PRIME,i))

        con.commit()
        _dblog_info(f'factor id {i} set to prime')

        # numbers with this prime factor could be completed
        num_rows: list[NumberRow] = []
        _getnums_withfac(num_rows,row,con)

    for num_row in num_rows:
        completeNumber(num_row.id)

def setFactorComposite(i:int, test:bool):
    '''
    sets a factor (by ID) as proven composite
    exception if an error occurs
    test = run prp test to check against
    '''
    with _dbcon() as con:
        row = _getfaci(i,con)
        if row is None:
            raise FDBException(f'factor id {i} does not exist in database')
        if row.value.bit_length() <= PROVE_BIT_LIM:
            raise FDBException(f'factor is small enough for primality proving')

        was_prime = (row.primality == Primality.PRIME)

        if test and prpTest(row.value):
            raise FDBException(f'factor id {i} prp test says it is prime,'
                               f' check if it is a BPSW pseudoprime?')
        con.execute("update factors set primality = %s, "
                    "modified = default where id = %s;",
                    (Primality.COMPOSITE,i))

        con.commit()
        _dblog_info(f'factor id {i} set to composite')

        # uncomplete numbers if switching from prime to composite
        # (necessary if number is incorrectly set as prime)
        num_rows: list[NumberRow] = []
        if was_prime:
            _getnums_withfac(num_rows,row,con)

        for num_row in num_rows:
            con.execute("update numbers set complete = false, "
                        "modified = default where id = %s;",(num_row.id,))
        con.commit()

def _get_facfac_helper(row:FactorRow|None,con:psycopg.Connection) \
        -> None|list[tuple[int,int,int]]:
    # helper function to get factorization of a factor
    if row is None:
        return None

    ret: list[tuple[int,int,int]] = []
    f_row = row
    while True:

        if f_row.f1_id is None: # does not split into 2 factors
            assert f_row.f2_id is None, f'internal error: f_row={f_row}'
            ret.append((f_row.value,f_row.primality,f_row.id))
            break

        else: # splits into 2 factors, append smaller
            assert f_row.f2_id is not None, f'internal error: f_row={f_row}'
            f1_row = _getfaci(f_row.f1_id,con)
            f2_row = _getfaci(f_row.f2_id,con)
            assert f1_row is not None, f'internal error: f_row={f_row}'
            assert f2_row is not None, f'internal error: f_row={f_row}'
            ret.append((f1_row.value,f1_row.primality,f1_row.id))
            # repeat splitting step on larger factor
            f_row = f2_row

    if DEBUG_EXTRA:
        prod = 1
        for f,_,_ in ret:
            prod *= f
        assert prod == row.value, f'internal error: row={row}'

    return ret

def _get_numfac_helper(n_row:NumberRow|None,con:psycopg.Connection) \
        -> None|list[tuple[int,int,None|int]]:
    # helper function to get factorization of a number
    if n_row is None:
        return None

    # small prime factors
    ret1: list[tuple[int,int,None|int]] = []
    for p in n_row.spfs:
        ret1.append((p,Primality.PRIME,None))
    cof_id = n_row.cof_id

    # large factors
    ret2 = None if cof_id is None else \
        _get_facfac_helper(_getfaci(cof_id,con),con)
    ret = ret1 if ret2 is None else ret1+ret2

    if DEBUG_EXTRA:
        prod = 1
        for f,_,_ in ret:
            prod *= f
        assert prod == n_row.value, f'internal error: n_row={n_row}'

    return ret

def getNumberFactorizationByValue(n:int) -> None|list[tuple[int,int,None|int]]:
    '''
    builds the current factorization data for a number, finding by value
    returns none if number does not exist
    returns a list of (factor,primality,id) tuples, or none if not in database
    id is none for small factors
    '''
    if n <= 0:
        return None
    with _dbcon() as con:
        return _get_numfac_helper(_getnumv(n,con),con)

def getNumberFactorizationByID(i:int) -> None|list[tuple[int,int,None|int]]:
    '''
    builds the current factorization data for a number, finding by id
    returns none if number does not exist
    returns a list of (factor,primality,id) tuples, or none if not in database
    id is none for small factors
    '''
    with _dbcon() as con:
        return _get_numfac_helper(_getnumi(i,con),con)

def _addfac(f:int) -> FactorRow:
    # return factor row, inserting factor if it is not in database
    assert f > 1, 'internal error'
    f_b = _int_to_dbnum(f)
    with _dbcon() as con:
        cur = con.execute("select * from factors where value = %s;",(f_b,))
        f_row = cur.fetchone()
        if f_row is not None:
            return FactorRow(f_row)

        # does not exist, insert new factor
        f_p = _dbprp(f)
        cur = con.execute("insert into factors (value,primality) "
                          "values (%s,%s) returning *;",(f_b,f_p))
        row = cur.fetchone()
        assert row is not None, 'internal error'
        con.commit()
        ret = FactorRow(row)
        _dblog_info(f'added factor id {ret.id}')
        if DEBUG_EXTRA:
            _dblog_debug(f'added factor {ret.value}')
        if ret.value.bit_length() <= 64:
            _dblog_warn(f'inserted small factor {ret.value} '
                        f'({ret.value.bit_length()} bits)')
        return ret

def _addfacs(i:int,fs:Iterable[int]):
    # try provided factors to make progress on cofactor of number id i
    with _dbcon() as con:
        for f in sorted(fs):

            # get the current cofactor
            row = _getnumi(i,con)
            assert row is not None, 'internal error'
            if row.cof_id is None:
                break
            cof = _getfaci(row.cof_id,con)
            assert cof is not None, 'internal error'

            # try to factor it
            try:
                addFactor(cof.value,f)
            except:
                pass

def addNumber(n:int,fs:Iterable[int]=[]) -> tuple[bool,NumberRow]:
    '''
    adds a number to the database, exception if n <= 0 or above size limit
    returns a tuple (True/False for if it was newly added, the row object)
    optional list of prime factors below 2**64 to begin factoring
    for production, try to find all factors below 2**64 before inserting
    '''
    if n < 1:
        raise FDBException('database only stores positive numbers')
    if n.bit_length() > NUM_BIT_LIM:
        raise FDBException('number exceeds size limit '
                           f'({n.bit_length()} > {NUM_BIT_LIM})')
    if DEBUG_EXTRA:
        _dblog_debug(f'calling addNumber n={n} fs={fs}')

    with _dbcon() as con:

        # check if number already exists
        row = _getnumv(n,con)
        if row is not None:
            _addfacs(row.id,fs)
            return (False,row)
        # note: checking this before insert into numbers should avoid (most?)
        # gaps in id column but this is not necessary
        # factor ids will get gaps when attempting to insert an existing factor

        # use provided factors to make factorization progress
        cof = n
        spfs: list[int] = []
        fs_large: list[int] = []
        for f in sorted(fs):

            if f.bit_length() <= 64:
                if not primeTest(f):
                    raise FDBException(f'provided non prime factor {f}')
                while cof % f == 0:
                    spfs.append(f)
                    cof //= f

            else: # factors bigger than 64 bit
                fs_large.append(f)

        # prepare factor values to store in database
        spf2b,spf4b,spf8b = _spfs_to_dblists(spfs)

        # put remaining cofactor in factors table
        cof_id: int|None = None
        if cof != 1:
            cof_id = _addfac(cof).id

        # add number
        cur = con.execute("insert into numbers "
                          "(value,spf2,spf4,spf8,cof_id) "
                          "values (%s,%s,%s,%s,%s) returning *;",
                          (_int_to_dbnum(n),spf2b,spf4b,spf8b,cof_id))
        row = NumberRow(cur.fetchone())
        con.commit()
        _dblog_info(f'number id {row.id} added with cofactor id {cof_id}')
        if DEBUG_EXTRA:
            _dblog_debug(f'number {n} = {spfs} {cof}')

    # attempt to use large provided factors
    _addfacs(row.id,fs_large)

    # attempt to complete
    completeNumber(row.id)
    return (True,row)

def deleteNumberByID(i:int) -> bool:
    '''
    delete a number from the database (by ID)
    returns true if this ID does not exist or it is successfully removed
    '''
    with _dbcon() as con:
        try:
            cur = con.execute("delete from numbers where id = %s "
                              "returning id;",(i,))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                _dblog_info(f'deleted number id {row[0]}')
            return True
        except:
            return False

def deleteNumberByValue(n:int) -> bool:
    '''
    delete a number from the database (by value)
    returns true if thihs value does not exist or it is successfully removed
    '''
    with _dbcon() as con:
        try:
            cur = con.execute("delete from numbers where value = %s "
                              "returning id;",(_int_to_dbnum(n),))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                _dblog_info(f'deleted number id {row[0]}')
            return True
        except:
            return False

def _addfac_try(n:int,*fs:int):
    # try adding factor from a list, ignoring exceptions (for recursive calls)
    for f in sorted(fs):
        try:
            addFactor(n,f)
            # if successful, take the same list and try on the cofactor
            _addfac_try(n//f,*fs)
            break
        except:
            pass

def _get_dbf_recur_large(mults:dict[int,int],i:int|None,
                         con:psycopg.Connection):
    # recursively find all factors starting with a divisor
    if i is None or i in mults:
        return

    row = _getfaci(i,con)
    assert row is not None, 'internal error'
    mults[i] = row.value

    # numbers with i in its primary factorization
    cur = con.execute("select id from factors where f1_id = %s or f2_id = %s;",
                      (i,i))
    for row in cur.fetchall():
        _get_dbf_recur_large(mults,row[0],con)

    # numbers with i in a secondary factorization
    cur = con.execute("select fac_id from factors_old "
                      "where f1_id = %s or f2_id = %s;",(i,i))
    for row in cur.fetchall():
        _get_dbf_recur_large(mults,row[0],con)

def addFactor(n:int, f:int):
    '''
    factors a number n in the factor database with a factor f
    exception if n not in database, invalid factor, or not a new factor
    '''
    if not (1 < f < n) or n % f != 0:
        raise FDBException('invalid factorization')

    # n = f * g with f <= g
    g = n // f
    if f > g:
        f,g = g,f
    if DEBUG_EXTRA:
        assert f <= g, f'internal error: n={n},f={f}'
        assert f*g == n, f'internal error: n={n},f={f}'
        _dblog_debug(f'calling addFactor n={n} f={f}')

    # check if new factorization should be stored
    with _dbcon() as con:

        # factor details for n
        n_row = _getfacv(n,con)
        if n_row is None:
            raise FDBException('n not in database')

        assert n_row.primality != Primality.PRIME, 'cannot factor a prime'
        assert n_row.primality != Primality.PROBABLE, 'bpsw pseudoprime found?'

        # no factor of n stored yet
        if n_row.f1_id is None:
            assert n_row.f2_id is None, 'internal error'
            better = True
            nf1 = None
            nf2 = None

        # get factors, check for f < nf1 (better than existing)
        else:
            # get existing factors nf1*nf2 == n
            cur = con.execute("select value from factors where id = %s;",
                              (n_row.f1_id,))
            nf1 = _dbnum_to_int(cur.fetchone()[0]) # type:ignore
            cur = con.execute("select value from factors where id = %s;",
                              (n_row.f2_id,))
            nf2 = _dbnum_to_int(cur.fetchone()[0]) # type:ignore

            if DEBUG_EXTRA:
                assert nf1 * nf2 == n, 'internal error'

            if f < nf1: # will replace factorization
                better = True
                # store old factorization in factors_old table
                con.execute("insert into factors_old (fac_id,f1_id,f2_id) "
                            "values (%s,%s,%s);",
                            (n_row.id,n_row.f1_id,n_row.f2_id))
                _dblog_info(f'replacing factorization of id {n_row.id} '
                            f'to {n_row.f1_id} and {n_row.f2_id}')
                if DEBUG_EXTRA:
                    _dblog_debug(f'replacing {n} = {nf1} * {nf2}')
            else:
                better = False

        if not better:
            raise FDBException('not a new factor result')

        # store factors in database
        f_row = _addfac(f)
        g_row = _addfac(g)

        # update factorization for n
        con.execute("update factors set f1_id = %s, f2_id = %s, "
                    "modified = default, primality = %s where id = %s;",
                    (f_row.id,g_row.id,Primality.COMPOSITE,n_row.id))

        con.commit()
        _dblog_info(f'factored id {n_row.id} to {f_row.id} and {g_row.id}')
        if DEBUG_EXTRA:
            _dblog_debug(f'factored {n_row.value} = {f} * {g}')

        # numbers containing this factor may be completed
        num_rows: list[NumberRow] = []
        _getnums_withfac(num_rows,n_row,con)

    # (database connection released to avoid multiple connections in recursion)

    # TODO find a better way to update factors with few operations
    # the few rules below do not guarantee best factor results on all
    # until running completeFactor() with full prime factorization
    # a few rules should cover most expected cases that occur in production
    # top priority is to ensure the factorization sequence goes from small to
    # large and the full known factorization can be found from any number

    # it should work fine in the expected ecm scenario
    # - ecm finds larger factor then a smaller one later
    # - factors will almost certainly be prime
    # - smaller factor replaces a larger one rarely (maybe only once or twice)

    # many related numbers sharing factors (such as repunits) is possible
    # - for something like this, better to use gcd in separate program

    # maybe it is not appropriate to design the database application to handle
    # the complexities of all various situations that could happen
    # - instead use specialized programs for analysis of particular numbers

    # try using old factor results to factor the new cofactor
    with _dbcon() as con:
        old_pairs_id = _getoldfac(n_row.id,con)
        old_pairs_value: list[tuple[int,int]] = []
        old_facs: list[int] = []
        for i,j in old_pairs_id:
            row = _getfaci(i,con)
            assert row is not None, 'internal error'
            old_facs.append(row.value)
            row2 = _getfaci(j,con)
            assert row2 is not None, 'internal error'
            old_pairs_value.append((row.value,row2.value))
    _addfac_try(g,*old_facs)

    # try old factor pairs with new factor pair to find factors
    for nf1,nf2 in old_pairs_value:
        if DEBUG_EXTRA:
            assert nf1 * nf2 == n, 'internal error'
            assert f < nf1 <= nf2 < g, 'internal error'
        _addfac_try(nf1,f)
        _addfac_try(nf2,f)
        _addfac_try(g,nf1)
        _addfac_try(g,nf2)

    # check for higher multiplicity
    while f < g and g % f == 0:
        _addfac_try(g,f)
        g //= f

    # recursively apply factorization to numbers with n as a factor
    with _dbcon() as con:
        dbf: dict[int,int] = {}
        _get_dbf_recur_large(dbf,n_row.id,con)
    for i in dbf:
        if i != n_row.id:
            _addfac_try(dbf[i],f)

    # attempt completion of the numbers found previously
    for num_row in num_rows:
        completeNumber(num_row.id)

def deleteFactorByID(i:int) -> bool:
    '''
    delete a factor from the database (by ID)
    returns true if this ID does not exist or it is successfully removed
    '''
    with _dbcon() as con:
        try:
            cur = con.execute("delete from factors where id = %s "
                              "returning id;",(i,))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                _dblog_info(f'deleted factor id {row[0]}')
            return True
        except:
            return False

def deleteFactorByValue(f:int) -> bool:
    '''
    delete a factor from the database (by value)
    returns true if this value does not exist or it is successfully removed
    '''
    with _dbcon() as con:
        try:
            cur = con.execute("delete from factors where value = %s "
                              "returning id;",(_int_to_dbnum(f)))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                _dblog_info(f'deleted factor id {row[0]}')
            return True
        except:
            return False

def _getoldfac(i:int,con:psycopg.Connection) -> list[tuple[int,int]]:
    # returns old factor pairs for factor id i, empty list if no factor id i
    cur = con.execute("select f1_id,f2_id from factors_old "
                      "where fac_id = %s;",(i,))
    return cur.fetchall()

def getOldFactors(i:int) -> list[tuple[int,int]]:
    '''
    get a list of factor ID pairs for old factorizations
    '''
    with _dbcon() as con:
        return _getoldfac(i,con)

def _get_dbf_recur_small(divs:dict[int,int],i:int|None,
                         con:psycopg.Connection):
    # recursively find all divisors starting with a factor
    if i is None or i in divs:
        return

    row = _getfaci(i,con)
    assert row is not None, 'internal error'
    divs[i] = row.value

    # primary factorization
    _get_dbf_recur_small(divs,row.f1_id,con)
    _get_dbf_recur_small(divs,row.f2_id,con)

    # secondary factorizations
    for f1_id,f2_id in _getoldfac(i,con):
        _get_dbf_recur_small(divs,f1_id,con)
        _get_dbf_recur_small(divs,f2_id,con)

def completeNumber(i:int) -> bool:
    '''
    mark number (by id) as completely factored
    consolidate all 64 bit prime factors into the row storage
    returns true if full prime factorization is known, false otherwise
    (this function should not need to be called manually)
    '''
    if DEBUG_EXTRA:
        _dblog_debug(f'calling completeNumber on number id {i}')

    with _dbcon() as con:
        n_row = _getnumi(i,con)
        if n_row is None:
            raise FDBException(f'no number with id {i}')
        if n_row.complete:
            return True
        factors = _get_numfac_helper(n_row,con)
        assert factors is not None, 'internal error'

    if DEBUG_EXTRA:
        prod = 1
        for factor,_,_ in factors:
            prod *= factor
        assert prod == n_row.value, 'internal error'

    completed = all(primality == Primality.PRIME for _,primality,_ in factors)

    # prepare consolidated small factors
    # these may be out of order if a smaller one is found after a larger one
    spfs: list[int] = []
    cof = n_row.value
    for factor,primality,f_id in factors:
        if factor.bit_length() <= 64 and primality == Primality.PRIME:
            spfs.append(factor)
            cof //= factor
            if DEBUG_EXTRA:
                assert primeTest(factor), 'internal error'

    # store updated information
    with _dbcon() as con:

        # ensure the cofactor is in the factors table
        cof_id: int|None = None
        if cof != 1:
            cof_id = _addfac(cof).id

        spf2b,spf4b,spf8b = _spfs_to_dblists(spfs)
        con.execute("update numbers set spf2 = %s, spf4 = %s, spf8 = %s, "
                    "cof_id = %s, complete = %s, modified = default "
                    "where id = %s;",
                    (spf2b,spf4b,spf8b,cof_id,completed,i))
        con.commit()

    if completed:
        _dblog_info(f'completed factorization of number id {i}')
    return completed

def makeFactorProgress(i:int):
    '''
    use the known factorization to progress factoring of all divisors
    (this function may not be necessary and is currently unused)
    '''
    with _dbcon() as con:
        f_row = _getfaci(i,con)
        if f_row is None:
            raise FDBException(f'no factor with id {i}')
        factors = _get_facfac_helper(f_row,con)
        assert factors is not None, 'internal error'
        dbf: dict[int,int] = {}
        _get_dbf_recur_small(dbf,f_row.id,con)

    # use factors to make factoring progress
    # note those with a prime factor below 2**64, possibly remove from database
    for db_fac_id in dbf:
        db_fac_value = dbf[db_fac_id]
        for factor,primality,f_id in factors:
            if db_fac_value % factor != 0:
                continue
            if DEBUG_EXTRA and factor.bit_length() <= 64 \
                    and primality == Primality.PRIME:
                _dblog_debug(f'factor id {db_fac_id} value {db_fac_value} '
                             f'has small prime factor {factor}')
            try:
                addFactor(db_fac_value,factor)
            except:
                pass
            break

#===============================================================================
# other factorization functions
#===============================================================================

def factorWithFactorDB(n:int):
    '''
    get factors from factordb.com to use for making factoring progress
    if n is newly created on factordb.com then it may have to be queried later
    exception if n is not in database or an error occurs with factordb.com
    '''
    with _dbcon() as con:
        nrow = _getnumv(n,con)
        if nrow is None:
            raise FDBException('number not in database')

    # query factordb.com and get list of factors
    resp = requests.get(_endpoint_factordb,{'query':str(n)})
    if not resp.ok:
        raise FDBException('invalid request to factordb.com')
    data = resp.json()

    # use these to make progress
    _addfacs(nrow.id,(int(f) for f,_ in data['factors']))

def _value_size_param(bitlen:int|None) -> tuple[int,bytes]:
    # return byte length and largest first byte value
    if bitlen is None:
        bitlen = NUM_BIT_LIM
    bytelen = (bitlen+7)//8
    extrabits = bitlen % 8
    firstbytemax = bytes([255 if extrabits == 0 else 2**(extrabits+1)-1])
    return bytelen,firstbytemax

def smallestUnknowns(limit:int|None=None, maxbits:int|None=None) \
            -> Generator[FactorRow,None,None]:
    '''
    find smallest factors which are not known to be either prime or composite
    '''
    maxbytes,firstbytemax = _value_size_param(maxbits)

    with _dbcon() as con:
        cur = con.execute("select * from factors where primality = %s "
                          "and length(value) <= %s and substr(value,1,1) <= %s "
                          "order by length(value), value limit %s;",
                          (Primality.UNKNOWN,maxbytes,firstbytemax,limit))
        for row in cur:
            yield FactorRow(row)

def smallestComposites(limit:int|None=None, maxbits:int|None=None) \
            -> Generator[FactorRow,None,None]:
    '''
    find smallest factors which are known to be composite and are not factored
    '''
    maxbytes,firstbytemax = _value_size_param(maxbits)

    with _dbcon() as con:
        cur = con.execute("select * from factors where primality = %s "
                          "and length(value) <= %s and substr(value,1,1) <= %s "
                          "and f1_id is null "
                          "order by length(value), value limit %s;",
                          (Primality.COMPOSITE,maxbytes,firstbytemax,limit))
        for row in cur:
            yield FactorRow(row)

def smallestProbablePrimes(limit:int|None=None, maxbits:int|None=None) \
            -> Generator[FactorRow,None,None]:
    '''
    find smallest factors which are probably prime but not proven yet
    '''
    maxbytes,firstbytemax = _value_size_param(maxbits)

    with _dbcon() as con:
        cur = con.execute("select * from factors where primality = %s "
                          "and length(value) <= %s and substr(value,1,1) <= %s "
                          "order by length(value), value limit %s;",
                          (Primality.PROBABLE,maxbytes,firstbytemax,limit))
        for row in cur:
            yield FactorRow(row)

#===============================================================================
# number categories
#===============================================================================

'''
factor tables are organized into categories, like filesystem directories
the root category is a directory represented by the empty tuple ()
other categories/tables are represented by a tuple of strings (path components)
categories store categories or tables, tables display factorizations
a table stores a sequence of numbers starting at an index >= 0

categories have a title for display and html info
they can also store an expression for nth terms which is currently unused
'''

class CategoryRow:
    '''
    object representation for a row in the categories table
    (row in "select * from categories")
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 10
            assert isinstance(row[0],int)
            assert isinstance(row[1],int)
            assert row[2] is None or isinstance(row[2],int)
            assert isinstance(row[3],str)
            assert isinstance(row[4],str)
            assert isinstance(row[5],bool)
            assert isinstance(row[6],str)
            assert row[7] is None or isinstance(row[7],str)
            assert isinstance(row[8],datetime)
            assert isinstance(row[9],datetime)
        self.id: int = row[0]
        self.parent_id: int = row[1]
        self.order_num: int|None = row[2]
        self.name: str = row[3]
        self.title: str = row[4]
        self.is_table: bool = row[5]
        self.info: str = row[6]
        self.expr: str|None = row[7]
        self.created: datetime = row[8]
        self.modified: datetime = row[9]

    def __repr__(self) -> str:
        return f'<CategoryRow(' \
            f'id={self.id},' \
            f'parent_id={self.parent_id},' \
            f'order_num={self.order_num},' \
            f'name={repr(self.name)},' \
            f'title={repr(self.title)},' \
            f'is_table={self.is_table},' \
            f'info={repr(self.info)},' \
            f'expr={repr(self.expr)}' \
            f'created={repr(self.created)},' \
            f'modified={repr(self.modified)})>'

def _str_to_path(s:str) -> tuple[str,...]:
    # convert path string to tuple of path components
    return tuple(p for p in s.strip(' \n\t/').split('/') if p)

def _path_to_str(p:tuple[str,...]):
    # convert path components to string
    return f'/{'/'.join(p)}'

def _getcati(i:int,con:psycopg.Connection) -> None|CategoryRow:
    # get category by id (from connection)
    cur = con.execute("select * from categories where id = %s;",(i,))
    row = cur.fetchone()
    return None if row is None else CategoryRow(row)

def _getcatp(path:tuple[str,...],con:psycopg.Connection) \
        -> None|list[CategoryRow]:
    # get categogry by path (from connection)
    row = _getcati(0,con)
    assert row is not None, 'internal error (root category never created)'
    ret = [row]

    for p in path:
        cur = con.execute("select * from categories "
                          "where parent_id = %s and name = %s;",
                          (row.id,p))
        row2 = cur.fetchone()
        if row2 is None:
            return None

        if DEBUG_EXTRA:
            assert cur.fetchone() is None, 'internal error (duplicate path)'

        row = CategoryRow(row2)
        ret.append(row)

    return ret

def _getcatpi(i:int,con:psycopg.Connection) -> None|list[CategoryRow]:
    # full category path details from id
    row = _getcati(i,con)
    if row is None:
        return None

    ret = [row]
    while row.id != 0:
        cur = con.execute("select * from categories where id = %s;",
                          (row.parent_id,))
        row2 = cur.fetchone()
        assert row2 is not None, 'internal error (parent does not exist)'

        if DEBUG_EXTRA:
            assert cur.fetchone() is None, 'internal error (duplicate id)'

        row = CategoryRow(row2)
        ret.append(row)

    # switch order to start at root
    return ret[::-1]

def getCategory(path:int|tuple[str,...]|str) -> None|CategoryRow:
    '''
    find category info by its path/id, empty tuple or 0 is root,
    none if it does not exist
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        if isinstance(path,tuple):
            data = _getcatp(path,con)
            return None if data is None else data[-1]
        else:
            return _getcati(path,con)

def getCategoryFullPath(path:int|tuple[str,...]|str) -> None|list[CategoryRow]:
    '''
    find info of a category and all its parents, empty path is root
    none if it does not exist
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        if isinstance(path,tuple):
            return _getcatp(path,con)
        else:
            return _getcatpi(path,con)

def _getcatpar(i:int,con:psycopg.Connection) -> None|CategoryRow:
    # get category parent
    cur = con.execute("select parent_id from categories where id = %s;",(i,))
    row = cur.fetchone()
    if row is None:
        return None
    return _getcati(row[0],con)

def getCategoryParent(i:int|tuple[str,...]|str) -> None|CategoryRow:
    '''
    find parent of category, parent of root is none,
    non if it does not exist
    '''
    if isinstance(i,str):
        i = _str_to_path(i)

    with _dbcon() as con:
        if isinstance(i,tuple):
            if i == ():
                return None
            data = _getcatp(i[:-1],con)
            return None if data is None else data[-1]
        else:
            return _getcatpar(i,con)

def _getcatchi(i:int,con:psycopg.Connection) -> list[CategoryRow]:
    # get category children (excluding root as a child of root)
    cur = con.execute("select * from categories where parent_id = %s "
                      "and id <> 0 order by order_num nulls last;",(i,))
    return [CategoryRow(row) for row in cur]

def listCategory(path:int|tuple[str,...]|str) -> None|list[CategoryRow]:
    '''
    list category children (by id)
    empty list if it does not exist
    empty list is still possible for categories that do exist
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        if isinstance(path,tuple):
            data = _getcatp(path,con)
            if data is None:
                return None
            return _getcatchi(data[-1].id,con)
        else:
            return _getcatchi(path,con)

def createCategory(path:tuple[str,...]|str, is_table:bool,
                   title:str, info:str) -> CategoryRow:
    '''
    creates a subcategory (cannot be root), its parent must exist
    exception if an error occurs
    returns row of new category
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    if path == ():
        raise FDBException('root category must be created in database setup')

    if not _path_name_re.fullmatch(path[-1]):
        raise FDBException(f'invalid path name: {repr(path[-1])}')

    with _dbcon() as con:

        # make sure parent category exists
        parent = _getcatp(path[:-1],con)
        if parent is None:
            raise FDBException('parent does not exist')
        parent = parent[-1]

        # create subcategory
        cur = con.execute("insert into categories "
                          "(parent_id,name,title,is_table,info) "
                          "values (%s,%s,%s,%s,%s) returning *;",
                          (parent.id,path[-1],title,is_table,info))

        new_row = CategoryRow(cur.fetchone())
        _dblog_info(f'created {'table' if is_table else 'category'} '
                    f'id {new_row.id} with path {_path_to_str(path)}')
        con.commit()
        return new_row

# prepare queries for the columns that may be updated in categories table
_setcat_q = dict()
for column in ('title','info','expr'):
    query = psycopg.sql.SQL("update categories set {} = %s, "
                            "modified = default where id = %s;")
    query = query.format(psycopg.sql.Identifier(column))
    _setcat_q[column] = query

def _setcat(path:int|tuple[str,...]|str,value,column:str):
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        if isinstance(path,tuple):
            pathdata = _getcatp(path,con)
            if pathdata is not None:
                pathdata = pathdata[-1]
        else:
            pathdata = _getcati(path,con)

        if pathdata is None:
            raise FDBException('category does not exist')

        con.execute(_setcat_q[column],(value,pathdata.id))
        con.commit()

        if isinstance(path,tuple):
            _dblog_info(f'updated {column} for {_path_to_str(path)}')
        else:
            _dblog_info(f'updated {column} for category id {path}')

def setCategoryInfo(path:int|tuple[str,...]|str, info:str):
    '''
    update the category info string
    '''
    _setcat(path,info,'info')

def setCategoryTitle(path:int|tuple[str,...]|str, title:str):
    '''
    update the category title string
    '''
    _setcat(path,title,'title')

def setCategoryExpr(path:int|tuple[str,...]|str, expr:str|None):
    '''
    update the category expression for generating terms
    '''
    _setcat(path,expr,'expr')

def renameCategory(old:tuple[str,...]|str, new:tuple[str,...]|str):
    '''
    moves/renames a category
    '''
    if isinstance(old,str):
        old = _str_to_path(old)
    if isinstance(new,str):
        new = _str_to_path(new)

    if old == () or new == ():
        raise FDBException('cannot rename root category')

    if not _path_name_re.fullmatch(new[-1]):
        raise FDBException('invalid path name')

    with _dbcon() as con:
        olddata = _getcatp(old,con)
        if olddata is None:
            raise FDBException('old path does not exist')
        newdata = _getcatp(new[:-1],con)
        if newdata is None:
            raise FDBException('new path parent does not exist')

        con.execute("update categories set parent_id = %s, order_num = null, "
                    "name = %s, modified = default where id = %s;",
                    (newdata[-1].id,new[-1],olddata[-1].id))
        con.commit()
        _dblog_info(f'renamed {_path_to_str(old)} to {_path_to_str(new)}')

def deleteCategory(path:tuple[str,...]|str):
    '''
    delete a category from the database
    exception if it does not exist or has children
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    if path == ():
        raise FDBException('cannot remove root category')

    with _dbcon() as con:
        data = _getcatp(path,con)
        if data is None:
            raise FDBException('path does not exist')

        con.execute('delete from categories where id = %s;',(data[-1].id,))
        con.commit()
        _dblog_info(f'deleted {_path_to_str(path)}')

def reorderSubcategories(path:tuple[str,...]|str, order:list[str]):
    '''
    changes listing order for subcategories
    exception if invalid order data or error occurs
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        data = _getcatp(path,con)
        if data is None:
            raise FDBException('path does not exist')

        children = _getcatchi(data[-1].id,con)
        if len(children) != len(order):
            raise FDBException('list size != number of children')
        if set(order) != set(child.name for child in children):
            raise FDBException('list does not match child categories')
        ordermap = {name:i for i,name in enumerate(order)}

        queryparams = [(ordermap[child.name],child.id) for child in children]
        con.cursor().executemany("update categories set order_num = %s "
                                 "where id = %s;",queryparams)
        con.commit()
        _dblog_info(f'reordered listing for {_path_to_str(path)}')

def _catwalk(row:CategoryRow,path:tuple[str,...],
             ret:list[tuple[tuple[str,...],CategoryRow]],
             con:psycopg.Connection):
    # recursively find children
    ret.append((path,row))
    children = _getcatchi(row.id,con)
    for child in children:
        _catwalk(child,path+(child.name,),ret,con)

def walkCategories(path:tuple[str,...]|str = ()) \
        -> list[tuple[tuple[str,...],CategoryRow]]:
    '''
    iterate a categories subtree, default starting at root
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        ret: list[tuple[tuple[str,...],CategoryRow]] = []
        data = _getcatp(path,con)
        if data is None:
            raise FDBException('path does not exist')
        _catwalk(data[-1],path,ret,con)
        return ret

def createCategoryNumber(path:tuple[str,...]|str, index:int,
                         value:int|str, expr:str):
    '''
    add a number to a category (must exist in database for integers >= 2)
    fs is the factor list passed to addNumber()
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        cat = _getcatp(path,con)
        if cat is None:
            raise FDBException('category does not exist')
        cat = cat[-1]
        if not cat.is_table:
            raise FDBException('numbers cat only be added to tables')

        # store string for numbers that cannot be in numbers table
        if isinstance(value,str) or value < 2:
            nid = None
            valstr = str(value)

        # make sure number exists and reference row
        else:
            num = _getnumv(value,con)
            if num is None:
                raise FDBException('number does not exist')
            nid = num.id
            valstr = None

        con.execute("insert into sequences (cat_id,index,num_id,value,expr) "
                    "values (%s,%s,%s,%s,%s);",
                    (cat.id,index,nid,valstr,expr))
        con.commit()
        _dblog_info(f'created {_path_to_str(path)} index {index}')

def updateCategoryNumber(path:tuple[str,...]|str, index:int, expr:str|None):
    '''
    updates the expression stored for a number
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        cat = _getcatp(path,con)
        if cat is None:
            raise FDBException('category does not exist')
        cat = cat[-1]
        if not cat.is_table:
            raise FDBException('category numbers are only in tables')

        cur = con.execute("update sequences set expr = %s "
                          "where cat_id = %s and index = %s returning *;",
                          (expr,cat.id,index))
        updated = cur.fetchone() is not None
        con.commit()
        if updated:
            _dblog_info(f'updated {_path_to_str(path)} index {index}')

def deleteCategoryNumber(path:tuple[str,...]|str, index:int):
    '''
    remove a number from a category
    also attempts to remove it from the database
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        cat = _getcatp(path,con)
        if cat is None:
            raise FDBException('category does not exist')
        cat = cat[-1]

        cur = con.execute("delete from sequences where cat_id = %s and "
                          "index = %s returning num_id;",(cat.id,index))
        row = cur.fetchone()
        con.commit()
        if row is not None:
            _dblog_info(f'deleted {_path_to_str(path)} index {index}')
            deleteNumberByID(row[0])

def getCategoryNumberInfo(path:tuple[str,...]|str, start:int, count:int) \
        -> list[tuple[int,str,str|NumberRow,list[tuple[int,int,None|int]]]]:
    '''
    gets all number table information for a category
    each is (index,expr,int|number_row,list[factor,primality,id])
    '''
    if isinstance(path,str):
        path = _str_to_path(path)

    with _dbcon() as con:
        cat = _getcatp(path,con)
        if cat is None:
            raise FDBException('category does not exist')
        cat = cat[-1]
        ret: list[tuple[int,str,str|NumberRow,list[tuple[int,int,None|int]]]] \
            = []

        cur = con.execute("select * from sequences where cat_id = %s "
                          "and %s <= index and index < %s "
                          "order by index;",(cat.id,start,start+count))
        for cat_id,index,num_id,value,expr in cur.fetchall():

            if DEBUG_EXTRA:
                assert cat_id == cat.id
                assert isinstance(index,int)
                assert num_id is None or isinstance(num_id,int)
                assert value is None or isinstance(value,str)
                assert expr is None or isinstance(expr,str)

            if expr is None:
                expr = ''

            if num_id is None: # number not stored in database
                ret.append((index,expr,value,[]))

            else: # number stored in database
                num = _getnumi(num_id,con)
                assert num is not None, 'internal error'
                factors = _get_numfac_helper(num,con)
                assert factors is not None, 'internal error'
                ret.append((index,expr,num,factors))

        return ret

def findCategoriesWithNumber(i:int) \
        -> list[tuple[CategoryRow,int,tuple[str,...]]]:
    '''
    list of (row,index,path) for categories containing number id i
    '''
    with _dbcon() as con:
        cur = con.execute("select cat_id,index from sequences "
                          "where num_id = %s;",(i,))
        cat_ids: list[tuple[int,int]] = cur.fetchall()
        ret: list[tuple[CategoryRow,int,tuple[str,...]]] = []

        for cat_id,index in cat_ids:
            row = _getcati(cat_id,con)
            path = _getcatpi(cat_id,con)
            assert row is not None, 'internal error'
            assert path is not None, 'internal error'
            ret.append((row,index,tuple(r.name for r in path[1:])))

        return ret

#===============================================================================
# user accounts
#===============================================================================

class UserRow:
    '''
    object representation for row in users table
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 11
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

def _gen_tkn() -> bytes:
    # 512 bit secure random token
    return secrets.token_bytes(64)

def _hash_b(b:bytes) -> bytes:
    # sha512 hash
    return hashlib.sha512(b).digest()

def _hmac(k:bytes,m:bytes) -> bytes:
    # hash based message authentication code
    # see wikipedia article for details
    # using sha512 (128 byte block, 64 byte hash)
    if len(k) > 128: # longer keys are hashed first
        kp = _hash_b(k)
    # shorter keys are zero padded to block size
    kp = k + b'\x00'*(128-len(k))
    x = bytes(byte ^ 0x5c for byte in kp) # k' ^ opad
    y = bytes(byte ^ 0x36 for byte in kp) # k' ^ ipad
    return _hash_b(x + _hash_b(y + m))

def _pbkdf2(pwd:bytes,salt:bytes,iters:int) -> bytes:
    # password based key derivation function
    # see wikipedia article for details (silghtly modified)
    assert iters > 0
    u = _hmac(pwd,salt)
    f = u
    for _ in range(iters-1):
        u = _hmac(pwd,u)
        f = bytes(f[i] ^ u[i] for i in range(64))
    return f

def _hash_tkn(tkn:bytes) -> bytes:
    # double sha512 to hash tokens
    return _hash_b(_hash_b(tkn))

def _hash_pwd(pwd:str,salt:bytes) -> bytes:
    # pbkdf2 to hash passwords (several iterations to be slightly slow)
    return _pbkdf2(pwd.encode(),salt,PWD_HASH_ITERS)

def createUser(username:str, email:str, pwd:str, fullname:str):
    '''
    create a user account, username and email must be unique
    '''
    if len(username) > 32:
        raise FDBException('username is too long')
    if len(email) > 64:
        raise FDBException('email is too long')
    if len(fullname) > 64:
        raise FDBException('fullname is too long')
    if not _username_re.fullmatch(username):
        raise FDBException('username contains invalid characters')
    if not _email_re.fullmatch(email):
        raise FDBException('email format is incorrect')

    pwd_salt = _gen_tkn()
    pwd_hash = _hash_pwd(pwd,pwd_salt)

    with _dbcon() as con:
        con.execute("insert into users (username,fullname,email,"
                    "pwd_hash,pwd_salt) values (%s,%s,%s,%s,%s);",
                    (username,fullname,email,pwd_hash,pwd_salt))
        con.commit()
        _dblog_info(f'created user {username} with email {email}')

def _getuser(u:int|str,con:psycopg.Connection) -> None|UserRow:
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

def getUser(user:str|int) -> None|UserRow:
    '''
    get user details from id, username, or email
    '''
    with _dbcon() as con:
        return _getuser(user,con)

def verifyUser(user:str|int, pwd:str, ip:str|None) -> None|UserRow:
    '''
    check user login both by id/username/email, none if invalid login
    '''
    # log some info to identify attempts of unauthorized access
    with _dbcon() as con:
        row = _getuser(user,con)
        if row is None:
            _dblog_warn(f'login attempt from {ip} (invalid user)')
            return None

        h = _hash_pwd(pwd,row.pwd_salt)
        valid = secrets.compare_digest(h,row.pwd_hash)
        if valid:
            _dblog_warn(f'verified login for {user} from {ip}')
            return row
        else:
            _dblog_warn(f'login attempt from {ip} '
                        f'(invalid password for {user})')
            return None

def changeUserPassword(user:str|int, new:str, old:str|None):
    '''
    change a password (to new), if old is not none then check it first
    exception if user does not exist or incorrect password
    '''
    with _dbcon() as con:
        row = _getuser(user,con)
        if row is None:
            raise FDBException('user does not exist')

        if len(new) < MIN_PWD_LEN:
            raise FDBException('minimum password length is '
                               f'{MIN_PWD_LEN} characters')

        if len(new) > 128:
            raise FDBException('maximum password length is 128 characters')

        if isinstance(old,str): # check old password first
            h = _hash_pwd(old,row.pwd_salt)
            valid = secrets.compare_digest(h,row.pwd_hash)
            if not valid:
                raise FDBException('old password is incorrect')

        newsalt = _gen_tkn()
        newhash = _hash_pwd(new,newsalt)

        con.execute("update users set pwd_hash = %s, pwd_salt = %s, "
                    "modified = default where id = %s;",
                    (newhash,newsalt,row.id))
        con.commit()
        _dblog_warn(f'changed password for user {row.username}')

def setUserDisabled(user:str, b:bool):
    '''
    set the disabled status of an account
    '''
    with _dbcon() as con:
        row = _getuser(user,con)
        if row is None:
            raise FDBException('user does not exist')
        con.execute("update users set is_disabled = %s, modified = default "
                    "where id = %s;",(b,row.id))
        if b:
            con.execute("delete from sessions where user_id = %s;",(row.id,))
        con.commit()
        _dblog_info(f'set user {user} as {'disabled' if b else 'enabled'}')

def setUserAdmin(user:str, b:bool):
    '''
    set the admin status of an account
    '''
    with _dbcon() as con:
        row = _getuser(user,con)
        if row is None:
            raise FDBException('user does not exist')
        con.execute("update users set is_admin = %s, modified = default "
                    "where id = %s;",(b,row.id))
        con.commit()
        _dblog_info(f'set user {user} as {'admin' if b else 'not admin'}')

def _getsess(th:bytes,con:psycopg.Connection) -> None|SessionRow:
    # th = token hash
    cur = con.execute("select * from sessions where token_hash = %s;",(th,))
    row = cur.fetchone()
    return None if row is None else SessionRow(row)

def _delsess(th:bytes,con:psycopg.Connection):
    # th = token hash
    con.execute("delete from sessions where token_hash = %s;",(th,))
    con.commit()

def getSession(token:bytes) -> None|SessionRow:
    '''
    get a session row if it exists and is not expired,
    if update then user/session timestamp details are modified
    '''
    with _dbcon() as con:
        token_hash = _hash_tkn(token)
        row = _getsess(token_hash,con)
        if row is None:
            return None
        if _now() < row.expires:
            return row
        else:
            _delsess(token_hash,con)
            return None

def updateSession(token:bytes, ip:str|None) -> datetime:
    '''
    update session expiration time, returns new expiration timestamp
    '''
    with _dbcon() as con:
        token_hash = _hash_tkn(token)
        exp = _now() + _sess_len
        con.execute("update sessions set accessed = default, last_ip = %s, "
                    "expires = %s where token_hash = %s;",
                    (ip,exp,token_hash))
        con.commit()
        return exp

def createSession(user:str, ip:str|None) -> str:
    '''
    create a login session for a user, returns the token for the cookie
    '''
    expires = _now() + _sess_len
    token = _gen_tkn()
    token_hash = _hash_tkn(token)
    with _dbcon() as con:
        row = _getuser(user,con)
        if row is None:
            raise FDBException('user does not exist')
        con.execute("insert into sessions (user_id,token_hash,expires,last_ip)"
                    "values (%s,%s,%s,%s);",
                    (row.id,token_hash,expires,ip))
        con.execute("update users set last_login = default where id = %s;",
                    (row.id,))
        con.commit()
        _dblog_info(f'created session for user {user} with token hash '
                    f'{token_hash.hex()[:10]}..')
        return token.hex()

def deleteSession(token:bytes):
    '''
    delete a login session
    '''
    h = _hash_tkn(token)
    with _dbcon() as con:
        cur = con.execute("delete from sessions where token_hash = %s "
                          "returning user_id;",(h,))
        row = cur.fetchone()
        if row is None:
            return
        con.commit()
        _dblog_info(f'deleted session for user id {row[0]} '
                    f'with token hash {h.hex()[:10]}..')

def deleteUser(user:str):
    '''
    delete a user account
    '''
    with _dbcon() as con:
        row = _getuser(user,con)
        if row is None:
            raise FDBException('user does not exist')
        con.execute("update users set username = null, email = null, "
                    "fullname = '', modified = default where id = %s;",
                    (row.id,))
        con.execute("delete from sessions where user_id = %s;",(row.id,))
        con.commit()
        _dblog_info(f'deleted user id {row.id}')

#===============================================================================
# contributions
#===============================================================================

def insertFactorForm(user:int|None, name:str, factors:str,
                     details:str, ip:str|None, fac_id:int|None):
    '''
    insert form data for factorization to be viewed later by admin
    '''
    with _dbcon() as con:
        con.execute("insert into submissions "
                    "(user_id,text_name,text_factors,"
                    "text_details,from_ip,fac_id) "
                    "values (%s,%s,%s,%s,%s,%s);",
                    (user,name,factors,details,ip,fac_id))
        con.commit()
        if user is None:
            _dblog_info(f'inserted anonymous factor submission')
        else:
            _dblog_info(f'inserted factor submission from user id {user}')

#===============================================================================
# other
#===============================================================================

def checkDatabaseConsistency():
    '''
    perform a full database consistency check
    for best results there should be no other database connections
    '''
    raise NotImplementedError()
