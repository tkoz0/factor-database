'''
get data from factordb.com to add to number factorization
'''

import requests

from app.database.connectionPool import FdbConnection
from app.database.numbers import \
    _getNumberById, \
    _getNumberByValue, \
    factorNumberByIdWithFactors, \
    factorNumberByValueWithFactors
from app.database.helpers import \
    FdbException, \
    stringToPath
from app.database.categories import _getCategoryByPath

FACTORDB_API_URL = 'https://factordb.com/api'

def factorNumberByIdWithFactorDB(i:int,/):
    '''
    get factors from factordb.com
    same as factorNumberByValueWithFactorDB but using number ID
    '''
    with FdbConnection() as con:
        n_row = _getNumberById(i,con)
        if n_row is None:
            raise FdbException('id not in database')
    if n_row.complete:
        return

    # query factordb.com and get list of factors
    resp = requests.get(FACTORDB_API_URL,{'query':str(n_row.value)})
    if not resp.ok:
        raise FdbException(f'invalid request to factordb.com: '
                           f'code={resp.status_code}, text={resp.text}')
    data = resp.json()

    factorNumberByIdWithFactors(i,(int(f) for f,_ in data['factors']))

def factorNumberByValueWithFactorDB(n:int,/):
    '''
    get factors from factordb.com to use for making factoring progress
    if n is newly created on factordb.com then it may have to be queried later
    exception if n is not in database or an error occurs with factordb.com
    '''
    with FdbConnection() as con:
        n_row = _getNumberByValue(n,con)
        if n_row is None:
            raise FdbException('number not in database')
    if n_row.complete:
        return

    # query factordb.com and get list of factors
    resp = requests.get(FACTORDB_API_URL,{'query':str(n)})
    if not resp.ok:
        raise FdbException(f'invalid request to factordb.com: '
                           f'code={resp.status_code}, text={resp.text}')
    data = resp.json()

    factorNumberByValueWithFactors(n,(int(f) for f,_ in data['factors']))

def factorCategoryIndexWithFactorDB(path:tuple[str,...]|str,index:int,/):
    '''
    attempts to make factor progress with factordb.com
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        cat = _getCategoryByPath(path,con)
        if cat is None:
            raise FdbException('category does not exist')
        cat = cat[-1]

        cur = con.execute("select num_id from sequences where cat_id = %s "
                          "and index = %s;",(cat.id,index))
        row = cur.fetchone()
        if row is None:
            raise FdbException('no number with that index')
        if row[0] is not None: # none for small exceptions
            factorNumberByIdWithFactorDB(row[0])
