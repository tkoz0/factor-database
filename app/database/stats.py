'''
database statistics
'''

from app.config import DB_NAME

from app.database.connectionPool import FdbConnection

def getDatabaseSize() -> int:
    '''
    database size in bytes (using pg_database_size)
    '''
    with FdbConnection() as con:
        cur = con.execute("select pg_database_size(%s);",(DB_NAME,))
        return cur.fetchone()[0] # type:ignore

def getNumbersCount() -> int:
    '''
    how many numbers are stored in database
    '''
    with FdbConnection() as con:
        cur = con.execute("select count(*) from numbers;")
        return cur.fetchone()[0] # type:ignore

def getFactorsCount() -> int:
    '''
    how many factors are stored in database
    '''
    with FdbConnection() as con:
        cur = con.execute("select count(*) from factors;")
        return cur.fetchone()[0] # type:ignore
