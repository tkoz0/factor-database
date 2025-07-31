'''
manages the tables storing numbers and factors
- numbers are taken from special sequences
- factors are intermediate (nontrivial) results
'''

import psycopg
from typing import \
    Generator, \
    Iterable

from app.database.connectionPool import FdbConnection
from app.database.helpers import \
    fdbNumberToInt, \
    intToFdbNumber, \
    fdbFormatToSpfs, \
    spfsToFdbFormat, \
    FdbException, \
    primeTest, \
    prpTest, \
    fdbPrimality
from app.database.constants import Primality
from app.database.logging import \
    logDatabaseInfoMessage, \
    logDatabaseWarnMessage, \
    logDatabaseDebugMessage

from app.config import \
    DEBUG_EXTRA, \
    PROVE_BIT_LIM, \
    NUM_BIT_LIM

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
    TODO document table columns
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 5
            assert isinstance(row[0],int)
            assert isinstance(row[1],bytes)
            assert isinstance(row[2],int)
            assert row[3] is None or isinstance(row[3],int)
            assert row[4] is None or isinstance(row[4],int)
        self.id: int = row[0]
        self.value: int = fdbNumberToInt(row[1])
        self.primality: int = row[2]
        self.f1_id: int|None = row[3]
        self.f2_id: int|None = row[4]

    def __repr__(self) -> str:
        return f'<FactorRow(id={self.id},' \
            f'value={self.value},' \
            f'primality={self.primality},' \
            f'f1_id={self.f1_id},' \
            f'f2_id={self.f2_id})>'

class NumberRow:
    '''
    object representation for row in numbers table
    (row in "select * from numbers")
    TODO document table columns
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 7
            assert isinstance(row[0],int)
            assert isinstance(row[1],bytes)
            assert row[2] is None or isinstance(row[2],bytes)
            assert row[3] is None or isinstance(row[3],bytes)
            assert row[4] is None or isinstance(row[4],bytes)
            assert row[5] is None or isinstance(row[5],int)
            assert isinstance(row[6],bool)
        self.id: int = row[0]
        self.value: int = fdbNumberToInt(row[1])
        n2,n4,n8 = fdbFormatToSpfs(row[2],row[3],row[4])
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

    def __repr__(self) -> str:
        return f'<NumberRow(' \
            f'id={self.id},' \
            f'value={self.value},' \
            f'spfs=[{','.join(map(str,self.spfs))}],' \
            f'cof_id={self.cof_id},' \
            f'complete={self.complete})>'

def _getNumberByValue(n:int,con:psycopg.Connection,/) -> None|NumberRow:
    # get number by value (from connection)
    cur = con.execute("select * from numbers where value = %s;",
                      (intToFdbNumber(n),))
    row = cur.fetchone()
    return None if row is None else NumberRow(row)

def getNumberByValue(n:int,/) -> None|NumberRow:
    '''
    returns the database row for a number (those to be factored)
    result is none if number is not in database
    '''
    if n < 2:
        return None
    with FdbConnection() as con:
        return _getNumberByValue(n,con)

def _getNumberById(i:int,con:psycopg.Connection,/) -> None|NumberRow:
    # get number by id (from connection)
    cur = con.execute("select * from numbers where id = %s;",(i,))
    row = cur.fetchone()
    return None if row is None else NumberRow(row)

def getNumberById(i:int,/) -> None|NumberRow:
    '''
    returns the database row for a number (those to be factored)
    result is none if number is not in database
    '''
    with FdbConnection() as con:
        return _getNumberById(i,con)

def _getFactorByValue(n:int,con:psycopg.Connection,/) -> None|FactorRow:
    # get factor by value (from connection)
    cur = con.execute("select * from factors where value = %s;",
                      (intToFdbNumber(n),))
    row = cur.fetchone()
    return None if row is None else FactorRow(row)

def getFactorByValue(n:int,/) -> None|FactorRow:
    '''
    returns the database row for a factor (intermediate results)
    result is none if factor is not in database
    '''
    if n <= 0:
        return None
    with FdbConnection() as con:
        return _getFactorByValue(n,con)

def _getFactorById(i:int,con:psycopg.Connection,/) -> None|FactorRow:
    # get factor by id (from connection)
    cur = con.execute("select * from factors where id = %s;",(i,))
    row = cur.fetchone()
    return None if row is None else FactorRow(row)

def getFactorById(i:int,/) -> None|FactorRow:
    '''
    returns the database row for a factor (intermediate results)
    result is none if factor is not in database
    '''
    with FdbConnection() as con:
        return _getFactorById(i,con)

def _getNumbersWithFactor(ret:list[NumberRow],row:FactorRow,
                     con:psycopg.Connection,/):
    # get numbers with factor i as a factor (primary factorization only)
    cur = con.execute("select * from numbers where cof_id = %s;",(row.id,))
    for nrow in cur.fetchall():
        ret.append(NumberRow(nrow))

    # numbers with current in its primary factorization
    cur = con.execute("select * from factors where f1_id = %s or f2_id = %s;",
                      (row.id,row.id))
    for frow in cur.fetchall():
        _getNumbersWithFactor(ret,FactorRow(frow),con)

    # numbers with current in a secondary factorization
    cur = con.execute("select factors.* from factors_old "
                      "join factors on factors_old.fac_id = factors.id "
                      "where factors_old.f1_id = %s or factors_old.f2_id = %s;",
                      (row.id,row.id))
    for frow in cur.fetchall():
        _getNumbersWithFactor(ret,FactorRow(frow),con)

def setFactorPrime(i:int,test:bool,/):
    '''
    sets a factor (by ID) as proven prime
    exception if an error occurs
    test = run prp test to check against
    '''
    with FdbConnection() as con:
        row = _getFactorById(i,con)
        if row is None:
            raise FdbException(f'factor id {i} does not exist in database')
        if row.value.bit_length() <= PROVE_BIT_LIM:
            raise FdbException(f'factor is small enough for primality proving')

        if test and not prpTest(row.value):
            raise FdbException(f'factor id {i} is actually composite')
        con.execute("update factors set primality = %s where id = %s;",
                    (Primality.PRIME,i))

        con.commit()
        logDatabaseInfoMessage(f'factor id {i} set to prime')

        # numbers with this prime factor could be completed
        num_rows: list[NumberRow] = []
        _getNumbersWithFactor(num_rows,row,con)

    for num_row in num_rows:
        completeNumber(num_row.id)

def setFactorProbable(i:int,test:bool,/):
    '''
    sets a factor (by ID) as probable prime
    exception if an error occurs
    test = run prp test to check against
    '''
    with FdbConnection() as con:
        row = _getFactorById(i,con)
        if row is None:
            raise FdbException(f'factor id {i} does not exist in database')
        if row.value.bit_length() <= PROVE_BIT_LIM:
            raise FdbException(f'factor is small enough for primality proving')

        was_prime = (row.primality == Primality.PRIME)

        if test and not prpTest(row.value):
            raise FdbException(f'factor id {i} is actually composite')
        con.execute("update factors set primality = %s where id = %s;",
                    (Primality.PROBABLE,i))

        con.commit()
        logDatabaseInfoMessage(f'factor id {i} set to probable')

        # uncomplete numbers if switching from prime
        # (not sure why this would ever happen)
        num_rows: list[NumberRow] = []
        if was_prime:
            _getNumbersWithFactor(num_rows,row,con)

        for num_row in num_rows:
            con.execute("update numbers set complete = false where id = %s;",
                        (num_row.id,))
        con.commit()

def setFactorComposite(i:int,test:bool,/):
    '''
    sets a factor (by ID) as proven composite
    exception if an error occurs
    test = run prp test to check against
    '''
    with FdbConnection() as con:
        row = _getFactorById(i,con)
        if row is None:
            raise FdbException(f'factor id {i} does not exist in database')
        if row.value.bit_length() <= PROVE_BIT_LIM:
            raise FdbException(f'factor is small enough for primality proving')

        was_prime = (row.primality == Primality.PRIME)

        if test and prpTest(row.value):
            raise FdbException(f'factor id {i} prp test says it is prime,'
                               f' check if it is a BPSW pseudoprime?')
        con.execute("update factors set primality = %s where id = %s;",
                    (Primality.COMPOSITE,i))

        con.commit()
        logDatabaseInfoMessage(f'factor id {i} set to composite')

        # uncomplete numbers if switching from prime to composite
        # (necessary if number is incorrectly set as prime)
        num_rows: list[NumberRow] = []
        if was_prime:
            _getNumbersWithFactor(num_rows,row,con)

        for num_row in num_rows:
            con.execute("update numbers set complete = false where id = %s;",
                        (num_row.id,))
        con.commit()

def _getFactorFactorizationHelper(row:FactorRow|None,
                                  con:psycopg.Connection,/) \
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
            f1_row = _getFactorById(f_row.f1_id,con)
            f2_row = _getFactorById(f_row.f2_id,con)
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

def _getNumberFactorizationHelper(n_row:NumberRow|None,
                                  con:psycopg.Connection,/) \
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
        _getFactorFactorizationHelper(_getFactorById(cof_id,con),con)
    ret = ret1 if ret2 is None else ret1+ret2

    if DEBUG_EXTRA:
        prod = 1
        for f,_,_ in ret:
            prod *= f
        assert prod == n_row.value, f'internal error: n_row={n_row}'

    return ret

def getNumberFactorizationByValue(n:int,/) \
        -> None|list[tuple[int,int,None|int]]:
    '''
    builds the current factorization data for a number, finding by value
    returns none if number does not exist
    returns a list of (factor,primality,id) tuples, or none if not in database
    id is none for small factors
    '''
    if n <= 0:
        return None
    with FdbConnection() as con:
        return _getNumberFactorizationHelper(_getNumberByValue(n,con),con)

def getNumberFactorizationById(i:int,/) -> None|list[tuple[int,int,None|int]]:
    '''
    builds the current factorization data for a number, finding by id
    returns none if number does not exist
    returns a list of (factor,primality,id) tuples, or none if not in database
    id is none for small factors
    '''
    with FdbConnection() as con:
        return _getNumberFactorizationHelper(_getNumberById(i,con),con)

def _addFactor(f:int,/) -> FactorRow:
    # return factor row, inserting factor if it is not in database
    assert f > 1, 'internal error'
    f_b = intToFdbNumber(f)
    with FdbConnection() as con:
        cur = con.execute("select * from factors where value = %s;",(f_b,))
        f_row = cur.fetchone()
        if f_row is not None:
            return FactorRow(f_row)

        # does not exist, insert new factor
        f_p = fdbPrimality(f)
        cur = con.execute("insert into factors (value,primality) "
                          "values (%s,%s) returning *;",(f_b,f_p))
        row = cur.fetchone()
        assert row is not None, 'internal error'
        con.commit()
        ret = FactorRow(row)
        logDatabaseInfoMessage(f'added factor id {ret.id}')
        if DEBUG_EXTRA:
            logDatabaseDebugMessage(f'added factor {ret.value}')
        if ret.value.bit_length() <= 64:
            logDatabaseWarnMessage(f'inserted small factor {ret.value} '
                        f'({ret.value.bit_length()} bits)')
        return ret

def _tryFactorById(i:int,fs:Iterable[int],/):
    # try provided factors to make progress on cofactor of number id i
    with FdbConnection() as con:
        for f in sorted(fs):

            # get the composite factors
            row = _getNumberById(i,con)
            assert row is not None, 'internal error'
            if row.cof_id is None:
                break
            factors = _getNumberFactorizationHelper(row,con)
            assert factors is not None, 'internal error'
            factors = [g for g,p,_ in factors
                       if p == Primality.UNKNOWN or p == Primality.COMPOSITE]

            # try to factor any composite
            for g in factors:
                try:
                    addFactor(g,f)
                except:
                    pass

def addNumber(n:int,fs:Iterable[int]=[],/) -> tuple[bool,NumberRow]:
    '''
    adds a number to the database, exception if n <= 0 or above size limit
    returns a tuple (True/False for if it was newly added, the row object)
    optional list of prime factors below 2**64 to begin factoring
    for production, try to find all factors below 2**64 before inserting
    '''
    if n < 1:
        raise FdbException('database only stores positive numbers')
    if n.bit_length() > NUM_BIT_LIM:
        raise FdbException('number exceeds size limit '
                           f'({n.bit_length()} > {NUM_BIT_LIM})')
    if DEBUG_EXTRA:
        logDatabaseDebugMessage(f'calling addNumber n={n} fs={fs}')

    with FdbConnection() as con:

        # check if number already exists
        row = _getNumberByValue(n,con)
        if row is not None:
            _tryFactorById(row.id,fs)
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
                    raise FdbException(f'provided non prime factor {f}')
                while cof % f == 0:
                    spfs.append(f)
                    cof //= f

            else: # factors bigger than 64 bit
                fs_large.append(f)

        # prepare factor values to store in database
        spf2b,spf4b,spf8b = spfsToFdbFormat(spfs)

        # put remaining cofactor in factors table
        cof_id: int|None = None
        if cof != 1:
            cof_id = _addFactor(cof).id

        # add number
        cur = con.execute("insert into numbers "
                          "(value,spf2,spf4,spf8,cof_id) "
                          "values (%s,%s,%s,%s,%s) returning *;",
                          (intToFdbNumber(n),spf2b,spf4b,spf8b,cof_id))
        row = NumberRow(cur.fetchone())
        con.commit()
        logDatabaseInfoMessage(
            f'number id {row.id} added with cofactor id {cof_id}')
        if DEBUG_EXTRA:
            logDatabaseDebugMessage(f'number {n} = {spfs} {cof}')

    # attempt to use large provided factors
    _tryFactorById(row.id,fs_large)

    # attempt to complete
    completeNumber(row.id)
    return (True,row)

def deleteNumberById(i:int,/) -> bool:
    '''
    delete a number from the database (by ID)
    returns true if this ID does not exist or it is successfully removed
    '''
    with FdbConnection() as con:
        try:
            cur = con.execute("delete from numbers where id = %s "
                              "returning id;",(i,))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                logDatabaseInfoMessage(f'deleted number id {row[0]}')
            return True
        except:
            return False

def deleteNumberByValue(n:int,/) -> bool:
    '''
    delete a number from the database (by value)
    returns true if this value does not exist or it is successfully removed
    '''
    with FdbConnection() as con:
        try:
            cur = con.execute("delete from numbers where value = %s "
                              "returning id;",(intToFdbNumber(n),))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                logDatabaseInfoMessage(f'deleted number id {row[0]}')
            return True
        except:
            return False

def _tryFactorByValue(n:int,fs:Iterable[int],/):
    # try adding factor from a list, ignoring exceptions (for recursive calls)
    for f in sorted(fs):
        try:
            addFactor(n,f)
            # if successful, take the same list and try on the cofactor
            _tryFactorByValue(n//f,fs)
            break
        except:
            pass

def _getMultiplesOfFactorById(mults:dict[int,int],i:int|None,
                              con:psycopg.Connection,/):
    # recursively find all factors starting with a divisor
    if i is None or i in mults:
        return

    row = _getFactorById(i,con)
    assert row is not None, 'internal error'
    mults[i] = row.value

    # numbers with i in its primary factorization
    cur = con.execute("select id from factors where f1_id = %s or f2_id = %s;",
                      (i,i))
    for row in cur.fetchall():
        _getMultiplesOfFactorById(mults,row[0],con)

    # numbers with i in a secondary factorization
    cur = con.execute("select fac_id from factors_old "
                      "where f1_id = %s or f2_id = %s;",(i,i))
    for row in cur.fetchall():
        _getMultiplesOfFactorById(mults,row[0],con)

def _getOldFactorizations(i:int,con:psycopg.Connection,/) \
        -> list[tuple[int,int]]:
    # returns old factor pairs for factor id i, empty list if no factor id i
    cur = con.execute("select f1_id,f2_id from factors_old "
                      "where fac_id = %s;",(i,))
    return cur.fetchall()

def addFactor(n:int,f:int,/):
    '''
    factors a number n in the factor database with a factor f
    exception if n not in database, invalid factor, or not a new factor
    '''
    if not (1 < f < n) or n % f != 0:
        raise FdbException('invalid factorization')

    # n = f * g with f <= g
    g = n // f
    if f > g:
        f,g = g,f
    if DEBUG_EXTRA:
        assert f <= g, f'internal error: n={n},f={f}'
        assert f*g == n, f'internal error: n={n},f={f}'
        logDatabaseDebugMessage(f'calling addFactor n={n} f={f}')

    # check if new factorization should be stored
    with FdbConnection() as con:

        # factor details for n
        n_row = _getFactorByValue(n,con)
        if n_row is None:
            raise FdbException('n not in database')

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
                logDatabaseInfoMessage(
                    f'replacing factorization of id {n_row.id} '
                    f'to {n_row.f1_id} and {n_row.f2_id}')
                if DEBUG_EXTRA:
                    logDatabaseDebugMessage(f'replacing {n} = {nf1} * {nf2}')
            else:
                better = False

        if not better:
            raise FdbException('not a new factor result')

        # store factors in database
        f_row = _addFactor(f)
        g_row = _addFactor(g)

        # update factorization for n
        con.execute("update factors set f1_id = %s, f2_id = %s, "
                    "primality = %s where id = %s;",
                    (f_row.id,g_row.id,Primality.COMPOSITE,n_row.id))

        con.commit()
        logDatabaseInfoMessage(
            f'factored id {n_row.id} to {f_row.id} and {g_row.id}')
        if DEBUG_EXTRA:
            logDatabaseDebugMessage(f'factored {n_row.value} = {f} * {g}')

        # numbers containing this factor may be completed
        num_rows: list[NumberRow] = []
        _getNumbersWithFactor(num_rows,n_row,con)

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
    with FdbConnection() as con:
        old_pairs_id = _getOldFactorizations(n_row.id,con)
        old_pairs_value: list[tuple[int,int]] = []
        old_facs: list[int] = []
        for i,j in old_pairs_id:
            row = _getFactorById(i,con)
            assert row is not None, 'internal error'
            old_facs.append(row.value)
            row2 = _getFactorById(j,con)
            assert row2 is not None, 'internal error'
            old_pairs_value.append((row.value,row2.value))
    _tryFactorByValue(g,old_facs)

    # try old factor pairs with new factor pair to find factors
    for nf1,nf2 in old_pairs_value:
        if DEBUG_EXTRA:
            assert nf1 * nf2 == n, 'internal error'
            assert f < nf1 <= nf2 < g, 'internal error'
        _tryFactorByValue(nf1,[f])
        _tryFactorByValue(nf2,[f])
        _tryFactorByValue(g,[nf1])
        _tryFactorByValue(g,[nf2])

    # check for higher multiplicity
    while f < g and g % f == 0:
        _tryFactorByValue(g,[f])
        g //= f

    # recursively apply factorization to numbers with n as a factor
    with FdbConnection() as con:
        dbf: dict[int,int] = {}
        _getMultiplesOfFactorById(dbf,n_row.id,con)
    for i in dbf:
        if i != n_row.id:
            _tryFactorByValue(dbf[i],[f])

    # attempt completion of the numbers found previously
    for num_row in num_rows:
        completeNumber(num_row.id)

def deleteFactorById(i:int,/) -> bool:
    '''
    delete a factor from the database (by ID)
    returns true if this ID does not exist or it is successfully removed
    '''
    with FdbConnection() as con:
        try:
            cur = con.execute("delete from factors where id = %s "
                              "returning id;",(i,))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                logDatabaseInfoMessage(f'deleted factor id {row[0]}')
            return True
        except:
            return False

def deleteFactorByValue(f:int,/) -> bool:
    '''
    delete a factor from the database (by value)
    returns true if this value does not exist or it is successfully removed
    '''
    with FdbConnection() as con:
        try:
            cur = con.execute("delete from factors where value = %s "
                              "returning id;",(intToFdbNumber(f)))
            row = cur.fetchone()
            con.commit()
            if row is not None:
                logDatabaseInfoMessage(f'deleted factor id {row[0]}')
            return True
        except:
            return False

def getOldFactors(i:int,/) -> list[tuple[int,int]]:
    '''
    get a list of factor ID pairs for old factorizations
    '''
    with FdbConnection() as con:
        return _getOldFactorizations(i,con)

def _getDivisorsOfFactorById(divs:dict[int,int],i:int|None,
                             con:psycopg.Connection,/):
    # recursively find all divisors starting with a factor
    if i is None or i in divs:
        return

    row = _getFactorById(i,con)
    assert row is not None, 'internal error'
    divs[i] = row.value

    # primary factorization
    _getDivisorsOfFactorById(divs,row.f1_id,con)
    _getDivisorsOfFactorById(divs,row.f2_id,con)

    # secondary factorizations
    for f1_id,f2_id in _getOldFactorizations(i,con):
        _getDivisorsOfFactorById(divs,f1_id,con)
        _getDivisorsOfFactorById(divs,f2_id,con)

def completeNumber(i:int,/) -> bool:
    '''
    mark number (by id) as completely factored
    consolidate all 64 bit prime factors into the row storage
    returns true if full prime factorization is known, false otherwise
    (this function should not need to be called manually)
    '''
    if DEBUG_EXTRA:
        logDatabaseDebugMessage(f'calling completeNumber on number id {i}')

    with FdbConnection() as con:
        n_row = _getNumberById(i,con)
        if n_row is None:
            raise FdbException(f'no number with id {i}')
        if n_row.complete:
            return True
        factors = _getNumberFactorizationHelper(n_row,con)
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
    with FdbConnection() as con:

        # ensure the cofactor is in the factors table
        cof_id: int|None = None
        if cof != 1:
            cof_id = _addFactor(cof).id

        spf2b,spf4b,spf8b = spfsToFdbFormat(spfs)
        con.execute("update numbers set spf2 = %s, spf4 = %s, spf8 = %s, "
                    "cof_id = %s, complete = %s where id = %s;",
                    (spf2b,spf4b,spf8b,cof_id,completed,i))
        con.commit()

    if completed:
        logDatabaseInfoMessage(f'completed factorization of number id {i}')
    return completed

def makeFactorProgress(i:int,/):
    '''
    use the known factorization to progress factoring of all divisors
    (this function may not be necessary and is currently unused)
    '''
    with FdbConnection() as con:
        f_row = _getFactorById(i,con)
        if f_row is None:
            raise FdbException(f'no factor with id {i}')
        factors = _getFactorFactorizationHelper(f_row,con)
        assert factors is not None, 'internal error'
        dbf: dict[int,int] = {}
        _getDivisorsOfFactorById(dbf,f_row.id,con)

    # use factors to make factoring progress
    # note those with a prime factor below 2**64, possibly remove from database
    for db_fac_id in dbf:
        db_fac_value = dbf[db_fac_id]
        for factor,primality,f_id in factors:
            if db_fac_value % factor != 0:
                continue
            if DEBUG_EXTRA and factor.bit_length() <= 64 \
                    and primality == Primality.PRIME:
                logDatabaseDebugMessage(
                    f'factor id {db_fac_id} value {db_fac_value} '
                    f'has small prime factor {factor}')
            try:
                addFactor(db_fac_value,factor)
            except:
                pass
            break

def factorNumberByIdWithFactors(i:int,fs:Iterable[int],/):
    '''
    use a factor list to make progress on factoring a number
    '''
    with FdbConnection() as con:
        row = _getNumberById(i,con)
        if row is None:
            raise FdbException(f'no number with id {i} exists')
    if not row.complete:
        _tryFactorById(i,fs)

def factorNumberByValueWithFactors(n:int,fs:Iterable[int],/):
    '''
    use a factor list to make progress on factoring a number
    '''
    with FdbConnection() as con:
        row = _getNumberByValue(n,con)
        if row is None:
            raise FdbException(f'number does not exist in database')
    if not row.complete:
        _tryFactorById(row.id,fs)

def _maxBitParams(bitlen:int|None,/) -> tuple[int,bytes]:
    # return byte length and largest first byte value
    # used for filtering database queries of numbers by value
    if bitlen is None:
        bitlen = NUM_BIT_LIM
    bytelen = (bitlen+7)//8
    extrabits = bitlen % 8
    firstbytemax = bytes([255 if extrabits == 0 else 2**(extrabits+1)-1])
    return bytelen,firstbytemax

def _smallestNumbersOfType(maxcount:int|None,maxbits:int|None,status:int) \
        -> Generator[FactorRow,None,None]:
    # find smallest factors of a given incomplete status
    maxbytes,firstbytemax = _maxBitParams(maxbits)
    with FdbConnection() as con:
        # f1_id null applies for probable and unknown
        # composites should only be selected if not factored yet
        cur = con.execute("select * from factors where primality = %s "
                          "and length(value) <= %s and substr(value,1,1) <= %s "
                          "and f1_id is null "
                          "order by length(value), value limit %s;",
                          (status,maxbytes,firstbytemax,maxcount))
        for row in cur:
            yield FactorRow(row)

def smallestUnknowns(maxcount:int|None=None,maxbits:int|None=None) \
            -> Generator[FactorRow,None,None]:
    '''
    find smallest factors which are not known to be either prime or composite
    '''
    yield from _smallestNumbersOfType(maxcount,maxbits,Primality.UNKNOWN)

def smallestComposites(maxcount:int|None=None,maxbits:int|None=None) \
            -> Generator[FactorRow,None,None]:
    '''
    find smallest factors which are known to be composite and are not factored
    '''
    yield from _smallestNumbersOfType(maxcount,maxbits,Primality.COMPOSITE)

def smallestProbablePrimes(maxcount:int|None=None,maxbits:int|None=None) \
            -> Generator[FactorRow,None,None]:
    '''
    find smallest factors which are probably prime but not proven yet
    '''
    yield from _smallestNumbersOfType(maxcount,maxbits,Primality.PROBABLE)
