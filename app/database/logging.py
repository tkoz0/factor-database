'''
manages logging for changes to the database
'''

import os
import sys

from app.config import LOG_TO_FILE

from app.database.helpers import \
    currentTimeUtc, \
    timestampToString

from app.database.connectionPool import FdbConnection
from app.database.constants import LogLevel

LOG_DIR = f'{os.path.dirname(__file__)}/../../logs'
LOG_FILE = None
LOG_FILE_NAME = None

if LOG_TO_FILE:
    os.makedirs(LOG_DIR,exist_ok=True)
    LOG_FILE_NAME = timestampToString(currentTimeUtc())
    LOG_FILE = open(f'{LOG_DIR}/{LOG_FILE_NAME}.log','a')

def _writeStderr(s:str,/):
    ''' write to stderr '''
    print(s,file=sys.stderr,flush=True)

def logStderrMessage(s:str,/):
    ''' write a log message to stderr '''
    _writeStderr(f'[{__name__}] [{timestampToString(currentTimeUtc())}] {s}')

def logDatabaseMessage(s:str,saveToDb:bool,level:int,/):
    ''' write message to stderr, database table, and possibly a log file '''
    global _logfile
    logStderrMessage(s)
    if LOG_FILE is not None:
        print(f'[{timestampToString(currentTimeUtc())}] {s}',
              file=LOG_FILE,
              flush=True)
    if not saveToDb:
        return
    with FdbConnection() as con:
        con.execute("insert into logs (text,level) values (%s,%s);",(s,level))
        con.commit()

def logDatabaseDebugMessage(s:str,/):
    ''' log debug message (not saved in database) '''
    logDatabaseMessage(f'[DEBUG] {s}',False,LogLevel.INFO)

def logDatabaseInfoMessage(s:str,/):
    ''' log database info message '''
    logDatabaseMessage(f'[INFO] {s}',True,LogLevel.INFO)

def logDatabaseWarnMessage(s:str,/):
    ''' log database warning message '''
    logDatabaseMessage(f'[WARN] {s}',True,LogLevel.WARN)

def logDatabaseCritMessage(s:str,/):
    ''' log database critical message '''
    logDatabaseMessage(f'[CRIT] {s}',True,LogLevel.CRIT)

def closeLogging():
    global _logfile,_logname
    if LOG_FILE is not None and LOG_FILE_NAME is not None:
        LOG_FILE.close()
        if os.path.getsize(LOG_FILE_NAME) == 0:
            os.remove(LOG_FILE_NAME)
