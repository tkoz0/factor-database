#!/bin/python3

import argparse
import json
import os
import sys
import time
t_start = time.time()

scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

parser = argparse.ArgumentParser()
parser.add_argument('--no-recreate-database',help='skip drop/recreate database',action='store_true')
parser.add_argument('--individual-numbers',help='skip individual (uncategorized) numbers',action='store_true')
parser.add_argument('--no-users',help='skip creating user accounts',action='store_true')
parser.add_argument('--no-categories',help='skip creating sample categories',action='store_true')
parser.add_argument('--no-numbers',help='skip creating sample numbers',action='store_true')
parser.add_argument('--no-factors',help='skip adding some known factors',action='store_true')
parser.add_argument('--no-primes',help='disable setting some provable primes',action='store_true')
parser.add_argument('--no-composites',help='disable setting unknowns to composite',action='store_true')
args = parser.parse_args()

# recreate blank database from the schema
if not args.no_recreate_database:
    if os.path.exists('config.json'):
        os.remove('config.json')
    #os.system('sqlite3 database.sqlite3 < schema.sql')
    os.system(f'psql < {scriptdir}/make_sample_db.sql')
    con_str = 'postgres://test_fdb:test_fdb@localhost/test_fdb'
    os.system(f'psql "{con_str}" < {scriptdir}/../database/schema.sql')
    with open(f'{scriptdir}/../config.json','w') as f:
        json.dump({
            'debug_extra': True,
            'num_bit_lim': 65536,
            'pwd_hash_iters': 100,
            'session_len_days': 7,
            'renew_sessions': False,
            'min_pwd_len': 3,
            'prp_bit_lim': 8192,
            'prove_bit_lim': 512,
            'table_per_page_default': 20,
            'table_per_page_limit': 100,
            'max_content_length': 2**20,
            'max_factors_length': 2**16,
            'max_details_length': 2**18,
            'db_type': 'postgres',
            'db_host': 'localhost',
            'db_port': 5433,
            'db_user': 'test_fdb',
            'db_pass': 'test_fdb',
            'db_name': 'test_fdb',
            'db_con_lim': 8,
            'log_to_file': True,
            'admin_email': 'admin@example.com',
            'proxy_fix_mode': None,
            'proxy_fix_hops': 0
        },f,indent=4)

# import afterward because it creates a connection to the database
# requires database setup to be done and config.json to exist
import app.database as db

# ==============================================================================

def primeSieve(L:int) -> list[int]:
    '''
    returns a list of primes below L using odd sieve of eratosthenes
    '''
    if L <= 2:
        return []
    s = [True]*(L//2)
    i = 1
    while True:
        v = 2*i+1
        if v*v >= L:
            break
        if s[i]:
            for j in range(v*v//2,L//2,v):
                s[j] = False
        i += 1
    ret = [2]
    for i in range(1,L//2):
        if s[i]:
            ret.append(2*i+1)
    return ret

def _mp(ps) -> int:
    r = 1
    m = 2**61 - 1
    for p in ps:
        r = (r*p) % m
    return r

EXPECTED_LEN = 6542
EXPECTED_SUM = 202288087
EXPECTED_MOD = 561521233722712261
SMALL_PRIME_LIMIT = 2**16
SMALL_PRIMES_LIST = primeSieve(SMALL_PRIME_LIMIT)
assert len(SMALL_PRIMES_LIST) == EXPECTED_LEN, \
    f'expected length {EXPECTED_LEN}'
assert sum(SMALL_PRIMES_LIST) == EXPECTED_SUM, \
    f'expected sum {EXPECTED_SUM}'
assert _mp(SMALL_PRIMES_LIST) == EXPECTED_MOD, \
    f'expected product {EXPECTED_MOD}'
# map prime -> index in SMALL_PRIMES_LIST, can be used as a set
SMALL_PRIMES_INDEX = {p:i for i,p in enumerate(SMALL_PRIMES_LIST)}

def findSmallPrimeFactors(n:int) -> tuple[int,list[int]]:
    '''
    small prime factorization
    returns cofactor and list of small factors found
    cofactor is 1 if completely factored, otherwise it is a remaining cofactor
    cofactor may be between small prime limit and its square (proven prime)
    '''
    if n <= 0:
        return n,[]
    factors = []
    for p in SMALL_PRIMES_LIST:
        if p*p > n:
            break
        while n % p == 0:
            factors.append(p)
            n //= p
    if 1 < n < SMALL_PRIME_LIMIT:
        # complete factorization
        # limit could be raised to SMALL_PRIME_LIMIT**2
        # but this allows explicitly storing larger factors in database
        factors.append(n)
        n = 1
    return n,factors

def fibonacci(n:int) -> int:
    '''
    well known fibonacci sequence
    f(0)=0,f(1)=1,f(n)=f(n-1)+f(n-2)
    '''
    assert n >= 0
    if n == 0: return 0
    if n == 1: return 1
    a,b = 0,1
    for _ in range(n-1):
        a,b = b,a+b
    return b

def lucas(n:int) -> int:
    '''
    well known lucas sequence
    f(0)=2,f(1)=1,f(n)=f(n-1)+f(n-2)
    '''
    assert n >= 0
    if n == 0: return 2
    if n == 1: return 1
    a,b = 2,1
    for _ in range(n-1):
        a,b = b,a+b
    return b

def factorial(n:int) -> int:
    '''
    product of positive integers <= n, special case for 0
    0!=1,n!=n*(n-1)!
    '''
    assert n >= 0
    if n == 0: return 1
    ret = 1
    for i in range(1,n+1):
        ret *= i
    return ret

def primorial(n:int) -> int:
    '''
    product of primes <= n
    n#=product(p<=n|prime(p))
    '''
    assert n > 0
    ret = 1
    for i in primeSieve(n+1):
        ret *= i
    return ret

def compositorial(n:int) -> int:
    '''
    product of composites <= n
    produdct(c<=n|!prime(c))
    '''
    assert n > 0
    primes = set(primeSieve(n+1))
    ret = 1
    for i in range(1,n+1):
        if i not in primes:
            ret *= i
    return ret

def repunit(n:int, base:int) -> int:
    '''
    number containing n ones in given base
    (base**n-1)//(base-1) (geometric sum)
    '''
    assert base >= 2
    return (base**n-1)//(base-1)

# ==============================================================================

def addnum1(n:int,fs:list[int]=[]):
    # insert number to database
    try:
        # trial division up to 2^16 for everything
        _,spf = findSmallPrimeFactors(n)
        db.addNumber(n,spf+fs)
    except db.FDBException as e:
        print(f'number {n} already in database: {e}')

# individual numbers
if args.individual_numbers:
    print('adding small integers')
    for n in range(1,100): # small numbers
        addnum1(n)
    print('adding numbers near small prime limit')
    for n in range(2**16-20,2**16+20): # near small prime limit
        addnum1(n)
    print('adding numbers near small prime limit squared')
    for n in range(2**32-20,2**32+20): # near small prime limit squared
        addnum1(n)
    print('adding repunit related numbers')
    for n in range(1,100): # repunit
        addnum1(repunit(n,10))
        addnum1(10**n+1)
    print('adding factorial related numbers')
    for n in range(2,100): # factorial +- 1
        addnum1(factorial(n)-1)
        addnum1(factorial(n)+1)

def addfac(n:int,f:int):
    # add factor result, ignore errors
    try:
        db.addFactor(n,f)
    except db.FDBException as e:
        print(f'factor result n={n},f={f} not added: {e}')

# sample users
if not args.no_users:
    db.createUser('tkoz','tkoz@example.com','tkoz','Tom K')
    db.setUserAdmin('tkoz',True)
    db.createUser('admin','admin@example.com','admin','Administrator')
    db.setUserAdmin('admin',True)

    db.createUser('user','user@example.com','user','User User')
    db.createUser('test','test@example.com','test','Test Test')
    db.createUser('bkoz','bkoz@example.com','bkoz','Backup Koz')
    db.setUserDisabled('bkoz',True)

    for short,long in [
        ('aishia','Aishia'),
        ('yue','Yue Nagumo'),
        ('tohka','Tohka Yatogami'),
        ('mukuro','Mukuro Hoshimiya'),
        ('setsuna','Setsuna Yuuki'),
        ('umi','Umi Sonoda'),
        ('euphie','Euphyllia Magenta'),
        ('anis','Anisphia Wynn Palettia'),
        ('chisato','Chisato Nishikigi'),
        ('takina','Takina Inoue'),
        ('yuuka','Yuuka Hayase'),
        ('noa','Noa Ushio')
    ]:
        db.createUser(short,f'{short}@example.com',short,long)

    db.setUserAdmin('aishia',True)
    db.setUserAdmin('yue',True)
    db.setUserAdmin('yuuka',True)

# sample categories
if not args.no_categories:
    db.setCategoryTitle((),'Factor Tables')
    db.setCategoryInfo((),'<p>This is the root of the factor tables.</p>\n'
                       '<p>Factor tables are structured like a filesystem tree '
                       'with categories(directories) and tables(files).</p>\n')

    db.createCategory(('repunit',),False,'Repunit',
                      'These are numbers containing a single repeated digit.')
    for b in range(2,17):
        db.createCategory(('repunit',f'base{b}'),True,f'Base {b} Repunit',
                          f'Base {b} repunits have the form ({b}^n-1)/{b-1}')

    db.createCategory(('factorial',),False,
                      'Factorial','Numbers close to factorials.')
    db.createCategory(('factorial','+1'),True,
                      'Factorial Plus 1','n!+1')
    db.createCategory(('factorial','-1'),True,
                      'Factorial Minus 1','n!-1')

    db.createCategory(('near_repdigit',),False,
                      'Near Repdigit',
                      'Numbers with almost a single repeating digit.')
    db.createCategory(('near_repdigit','base2'),False,
                      'Near Repdigit Base 2','')
    db.createCategory(('near_repdigit','base10'),False,
                      'Near Repdigit Base 10','')
    db.createCategory(('near_repdigit','base2','100..001'),True,
                      'Near Repdigit Base 2: 100..001','nth term = 2^n+1')
    db.createCategory(('near_repdigit','base10','100..001'),True,
                      'Near Repdigit Base 10: 100..001','nth term = 10^n+1')
    db.createCategory(('near_repdigit','base10','100..003'),True,
                      'Near Repdigit Base 10: 100..003','nth term = 10^n+3')
    db.createCategory(('near_repdigit','base10','100..007'),True,
                      'Near Repdigit Base 10: 100..007','nth term = 10^n+7')
    db.createCategory(('near_repdigit','base10','100..009'),True,
                      'Near Repdigit Base 10: 100..009','nth term = 10^n+9')

    db.createCategory(('mersenne',),True,'Mersenne','2^p-1 where p is prime')
    db.createCategory(('fibonacci',),True,'Fibonacci','fibonacci numbers')
    db.createCategory(('lucas',),True,'Lucas','lucas numbers')

    db.createCategory(('empty',),False,'','')
    db.createCategory(('test',),False,'test title','test category')
    db.createCategory(('test','ecat'),False,'empty category','empty category')
    db.createCategory(('test','etab'),True,'empty table','empty table')

    def addnum2(path:tuple[str,...],index:int,value:int,expr:str):
        addnum1(value)
        db.createCategoryNumber(path,index,value,expr)

    # fill some categories with sample numbers
    if not args.no_numbers:
        primes = primeSieve(1000)
        for i in range(220):
            addnum2(('fibonacci',),i,fibonacci(i),f'\\(F_{{{i}}}\\)')
            addnum2(('lucas',),i,lucas(i),f'\\(L_{{{i}}}\\)')
        for i in range(110):
            addnum2(('mersenne',),i+1,2**primes[i]-1,f'\\(2^{{{primes[i]}}}-1\\)')
            addnum2(('repunit','base2'),i,repunit(i,2),f'\\({{2^{{{i}}}-1\\over2-1}}\\)')
            addnum2(('repunit','base10'),i,repunit(i,10),f'\\({{10^{{{i}}}-1\\over10-1}}\\)')
            addnum2(('repunit','base16'),i,repunit(i,16),f'\\[{{16^{{{i}}}-1\\over16-1}}\\]')
            addnum2(('factorial','+1'),i,factorial(i)+1,f'\\({i}!+1\\)')
            addnum2(('factorial','-1'),i,factorial(i)-1,f'\\({i}!-1\\)')
            if i > 0:
                addnum2(('near_repdigit','base2','100..001'),i,2**i+1,f'2^{i}+1')
                addnum2(('near_repdigit','base10','100..001'),i,10**i+1,f'10^{i}+1')
                addnum2(('near_repdigit','base10','100..003'),i,10**i+3,f'10^{i}+3')
                addnum2(('near_repdigit','base10','100..007'),i,10**i+7,f'10^{i}+7')
                addnum2(('near_repdigit','base10','100..009'),i,10**i+9,f'10^{i}+9')

        # add some known factors (depends on sample numbers)
        if not args.no_factors:
            # test for (10^72-1)/9, largest to smallest
            addfac(98641*333667*99990001*999999000001*3199044596370769,3199044596370769)
            addfac(98641*333667*99990001*999999000001,999999000001)
            addfac(98641*333667*99990001,99990001)
            addfac(98641*333667,333667)
            # 20!+1
            addfac(2432902008176640001,20639383)
            # 29!+1
            addfac(607389022033365525489016693,218568437)
            # 30!+1
            addfac(688877213180049028924242451,82561)
            addfac(8343857428810806905491,1080941)
            # 53!-1
            addfac(411878146648041773224589435724963835599801887307718828853646786781,34968116649159559)
            # 60!-1
            addfac(1135041210304377321549084870170967723469400164556165046030456649353376074205429,809394310478457594898676919366517)
            # (10^37-1)/9
            addfac(1111111111111111111111111111111111111,2028119)
            addfac(547853016076034547830334961169,247629013)
            # (10^49-1)/9
            addfac(1000000100000010000001000000100000010000001,505885997)
            # (10^60-1)/9
            addfac(481183553194557910201,2906161)
            addfac(165573604901641,4188901)
            # (10^92-1)/9
            addfac(469229935360571510991280627078200906912258332164075748377095948539772049526983,549797184491917)
            # (10^106-1)/9
            addfac(944019635608420655149627112243934673841215897290663645803832719720570187859907486075710374775795336543,1659431)
            # 2^71-1 (larger before smaller)
            addfac(228479*48544121*212885833,48544121)
            addfac(228479*212885833,212885833)
            # 2^211-1
            addfac(216613513765708687178959939782445929702196520191348629414679,60272956433838849161)
            # 2^223-1
            addfac(737134211930623934890004240362542534960276273378371862008629361,2916841)
            # factor lucas numbers 73,77,78
            addfac(1803423556807921,151549)
            addfac(2141890304401,229769)
            addfac(1111126318086721,90481)
            # 10^32+1
            addfac(5040068544932211078070661761,976193)
            addfac(5162983697826363309377,6187457)

        def getnumid(n:int) -> int:
            # get id for a number (must exist)
            row = db.getNumberByValue(n)
            assert row is not None
            return row.id

        def getfacid(f:int) -> int:
            # get id for a factor (must exist)
            row = db.getFactorByValue(f)
            assert row is not None
            return row.id

        # prove primality for some probable primes (depends on sample numbers)
        if not args.no_primes:
            # 2^179-1
            db.setFactorPrime(getfacid(1489459109360039866456940197095433721664951999121),True)
            # 2^197-1
            db.setFactorPrime(getfacid(26828803997912886929710867041891989490486893845712448833),True)
            # 2^211-1
            db.setFactorPrime(getfacid(3593875704495823757388199894268773153439),True)
            # 10^53+1
            db.setFactorPrime(getfacid(9090909090909090909090909090909090909090909090909091),True)
            # 10^67+1
            db.setFactorPrime(getfacid(909090909090909090909090909090909090909090909090909090909090909091),True)
            # 10^39+3
            db.setFactorPrime(getfacid(1000000000000000000000000000000000000003),True)
            # 10^56+3
            db.setFactorPrime(getfacid(100000000000000000000000000000000000000000000000000000003),True)
            # 10^59+3
            db.setFactorPrime(getfacid(104058272632674297606659729448491155046826222684703433923),True)

        # set some unknown numbers to composite (depends on sample numbers)
        if not args.no_composites:
            # 2^307-1
            db.setFactorComposite(getfacid(260740604970814219042361048116400404614587954389239840081425977517360806369707098391474864127),True)
            # 2^311-1
            db.setFactorComposite(getfacid(4171849679533027504677776769862406473833407270227837441302815640277772901915313574263597826047),True)
            # 2^313-1
            db.setFactorComposite(getfacid(16687398718132110018711107079449625895333629080911349765211262561111091607661254297054391304191),True)
            # 2^317-1
            db.setFactorComposite(getfacid(28072587476617996036103218722657345634038278340298769450465797600439224658035965592773657961),True)
            # 10^78+7
            db.setFactorComposite(getfacid(1000000000000000000000000000000000000000000000000000000000000000000000000000007),True)
            # 10^79+7
            db.setFactorComposite(getfacid(10000000000000000000000000000000000000000000000000000000000000000000000000000007),True)
            # 10^96+9
            db.setFactorComposite(getfacid(141943493147039122607524680070012208559845576834935473197732821750058232318063572800049737),True)
            # 10^97+9
            db.setFactorComposite(getfacid(10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000009),True)
            # 10^98+9
            db.setFactorComposite(getfacid(69783670621074668527564549895324494068387997208653175157013258897418004187020237264480111653873),True)

print(f'make sample database script done, {time.time()-t_start} sec')
