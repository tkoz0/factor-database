'''
manages a connection pool to reuse for accessing database
'''

import psycopg
import sys

from app.config import \
    DB_USER, \
    DB_HOST, \
    DB_NAME, \
    DB_PORT, \
    DB_PASS, \
    DB_CON_LIM

from app.database.helpers import FdbException

_CON_STRING = \
         f'postgres://{DB_USER}@{DB_HOST}/{DB_NAME}' if DB_PORT == 5432 \
    else f'postgres://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

def _makeConnection() -> psycopg.Connection:
    #return psycopg.connect(host=DB_HOST,port=DB_PORT,
    #                       user=DB_USER,password=DB_PASS,dbname=DB_NAME)
    return psycopg.connect(_CON_STRING,password=DB_PASS)

# reusable connection objects for any purpose
_CON_POOL: list[psycopg.Connection] = []
_CON_COUNT: int = 0

class FdbConnection:
    '''
    for handling database connection
    with FdbConnection() as con: ...
    caller must call con.commit() if doing write operations
    '''

    def __init__(self):
        self.con = None

    def __enter__(self) -> psycopg.Connection:
        global _CON_POOL, _CON_COUNT
        if _CON_POOL == []:
            if _CON_COUNT >= DB_CON_LIM:
                sys.stderr.write(
                    f'tried to open more than {DB_CON_LIM} connections\n')
                raise FdbException('exceeded database connection limit')
            self.con = _makeConnection()
            _CON_COUNT += 1
            sys.stderr.write(f'created connection, total is now {_CON_COUNT}\n')
        else:
            self.con = _CON_POOL.pop()
        return self.con

    def __exit__(self,exctyp,excval,traceback) -> None:
        #if exctyp is not None or excval is not None or traceback is not None:
        #    _stderr_log(f'_dbcon.__exit__ received {exctyp}: {excval}')
        #    _stderr_write(str(traceback))
        global _CON_POOL
        assert isinstance(self.con,psycopg.Connection)
        self.con.rollback()
        _CON_POOL.append(self.con)

def closeDatabaseConnections():
    global _CON_POOL, _CON_COUNT
    for con in _CON_POOL:
        con.close()
    _CON_POOL = []
    _CON_COUNT = 0

'''
old sqlite3 stuff
_con = sqlite3.connect('database.sqlite3')
_con.create_function('regexp',2,_regexp)
_con.execute('pragma foreign_keys = on;')
_cur = _con.cursor()
'''
