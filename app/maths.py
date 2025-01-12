import gmpy2
import cypari2

pari = cypari2.Pari()

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

# hardcoded number of primes below powers of 2
PTLENS = {
    4:2,
    8:4,
    16:6,
    32:11,
    64:18,
    128:31,
    256:54,
    512:97,
    1024:172,
    2048:309,
    4096:564,
    8192:1028,
    16384:1900,
    32768:3512,
    65536:6542,
    131072:12251,
    262144:23000,
    524288:43390,
    1048576:82025,
    2097152:155611,
    4194304:295947,
    8388608:564163,
    16777216:1077871,
    33554432:2063689,
    67108864:3957809,
    134217728:7603553,
    268435456:14630843,
    536870912:28192750,
    1073741824:54400028,
    2147483648:105097565,
    4294967296:203280221
}

# hardcoded sum of primes below powers of 2
PTSUMS = {
    4:5,
    8:17,
    16:41,
    32:160,
    64:501,
    128:1720,
    256:6081,
    512:22548,
    1024:80189,
    2048:289176,
    4096:1070091,
    8192:3908641,
    16384:14584641,
    32768:54056763,
    65536:202288087,
    131072:761593692,
    262144:2867816043,
    524288:10862883985,
    1048576:41162256126,
    2097152:156592635694,
    4194304:596946687124,
    8388608:2280311678414,
    16777216:8729068693022,
    33554432:33483086021512,
    67108864:128615914639624,
    134217728:494848669845962,
    268435456:1906816620981654,
    536870912:7357074544482779,
    1073741824:28422918403819825,
    2147483648:109930816131860852,
    4294967296:425649736193687430
}

# hardcoded product of primes below powers of 2 (modulo 2^61-1)
PTMULS = {
    4:6,
    8:210,
    16:30030,
    32:200560490130,
    64:1676695752428165655,
    128:821506709920287210,
    256:69823475035379291,
    512:577996834424406794,
    1024:1455449495097181675,
    2048:1036146577712543422,
    4096:1026573903930209107,
    8192:2266994784943692819,
    16384:102903200434065700,
    32768:709531303068170869,
    65536:561521233722712261,
    131072:1618290815257762622,
    262144:1599265766891171415,
    524288:2089577079781601737,
    1048576:797505266085355149,
    2097152:913470308901821748,
    4194304:863130153652352942,
    8388608:509955407725348394,
    16777216:639422569581799880,
    33554432:502114142505091523,
    67108864:690383256166316175,
    134217728:2033512217918383681,
    268435456:623180762266957225,
    536870912:184447419738215046,
    1073741824:297388947231001991,
    2147483648:1275041842188820459,
    4294967296:2175006135807333620
}

def _mp(ps) -> int:
    r = 1
    m = 2**61 - 1
    for p in ps:
        r = (r*p) % m
    return r

SMALL_PRIME_LIMIT = 2**16
SMALL_PRIMES_LIST = primeSieve(SMALL_PRIME_LIMIT)
assert len(SMALL_PRIMES_LIST) == PTLENS[SMALL_PRIME_LIMIT], \
    f'expected length {PTLENS[SMALL_PRIME_LIMIT]}'
assert sum(SMALL_PRIMES_LIST) == PTSUMS[SMALL_PRIME_LIMIT], \
    f'expected sum {PTSUMS[SMALL_PRIME_LIMIT]}'
assert _mp(SMALL_PRIMES_LIST) == PTMULS[SMALL_PRIME_LIMIT], \
    f'expected product {PTMULS[SMALL_PRIME_LIMIT]}'
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
        # but choosing to explicitly store these in database
        factors.append(n)
        n = 1
    return n,factors

def prpTest(n:int, k:int = 0) -> bool:
    '''
    probable prime test with gmpy2
    (bpsw test + up to k miller-rabin tests)
    (4096 bit primes take about 0.1sec on the vps for testing)
    '''
    assert k >= 0
    # gmp subtracts 24 from 2nd arg and runs up to that many miller-rabin tests
    return gmpy2.is_prime(n,24+k) # type:ignore

def primeTest(n:int) -> bool:
    '''
    provable prime test with pari/gp isprime binding
    use for small numbers that can be tested quickly
    (256 bit primes take about 0.05sec on the vps for testing)
    '''
    return bool(pari.isprime(n))

# possible number types that may be stored in the database =====================

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

def padovan(n:int) -> int:
    assert n >= 0
    if n == 0: return 1
    if n == 1: return 1
    if n == 2: return 1
    a,b,c = 1,1,1
    for _ in range(n-2):
        a,b,c = b,c,a+b
    return c

def narayana(n:int) -> int:
    assert n >= 0
    if n == 0: return 1
    if n == 1: return 1
    if n == 2: return 1
    a,b,c = 1,1,1
    for _ in range(n-2):
        a,b,c = b,c,a+c
    return c
