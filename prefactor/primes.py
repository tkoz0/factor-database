'''
code for handling things with primality

public interface:
- isPrp(n,k=0) test probable primality with gmp, bpsw + k miller rabin
- isPrime(n) test provable primality with pari/gp
- primeSieve(L) list primes below L
- nthPrime(n) nth prime (1-indexed), maintains cached results
- nthComposite(n) nth composite (1-indexed), maintains cached results
'''

import gmpy2
import cypari2
pari = cypari2.Pari()

def isPrp(n:int,k:int=0,/) -> bool:
    ''' probable prime test with gmpy2 (up to k miller rabin tests) '''
    assert k >= 0
    return gmpy2.is_prime(n,k+24) # type:ignore

def isPrime(n:int,/) -> bool:
    ''' proven primality test with cypari2 '''
    return pari.isprime(n)

def primeSieve(L:int,/) -> list[int]:
    ''' sieve primes below L, sorted list '''
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
    ret = [2, *(2*i+1 for i in range(1,L//2) if s[i])]
    return ret

_cache_primes: list[int] = []
_cache_primes_set: set[int] = set()
_cache_composites: list[int] = []
_cache_limit: int = 2

def _cache_expand():
    global _cache_primes,_cache_primes_set,_cache_composites,_cache_limit
    _cache_limit = (_cache_limit * 3 // 2) + 1
    _cache_primes = primeSieve(_cache_limit)
    _cache_primes_set = set(_cache_primes)
    _cache_composites = [n for n in range(2,_cache_limit)
                         if n not in _cache_primes_set]

def nthPrime(n:int,/) -> int:
    ''' nth prime (1-indexed starting with 2) '''
    global _cache_primes
    assert n > 0
    while n-1 >= len(_cache_primes):
        _cache_expand()
    return _cache_primes[n-1]

def nthComposite(n:int,/) -> int:
    ''' nth composite (1-indexed starting with 4) '''
    global _cache_composites
    assert n > 0
    while n-1 >= len(_cache_composites):
        _cache_expand()
    return _cache_composites[n-1]

if __name__ == '__main__':
    # tests

    primes = primeSieve(65536)
    primes_set = set(primes)
    assert primes == sorted(primes)
    assert len(primes) == 6542
    assert sum(primes) == 202288087
    assert min(primes) == 2 == primes[0]
    assert max(primes) == 65521 == primes[-1]
    assert all(isPrime(n) == (n in primes_set) for n in range(65536))
    assert all(isPrp(n) == (n in primes_set) for n in range(65536))
    assert [nthPrime(n) for n in range(1,11)] == [2,3,5,7,11,13,17,19,23,29]
    assert [nthComposite(n) for n in range(1,11)] == [4,6,8,9,10,12,14,15,16,18]
    assert nthPrime(1000) == 7919
    assert nthPrime(1001) == 7927
    assert nthPrime(10000) == 104729
    assert nthPrime(10001) == 104743
    assert nthComposite(1000) == 1197
    assert nthComposite(1001) == 1198
    assert nthComposite(1002) == 1199
    assert nthComposite(1003) == 1200
    assert nthComposite(1004) == 1202
    assert nthComposite(10000) == 11374
    assert nthComposite(10001) == 11375
