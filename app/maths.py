import gmpy2
import cypari2
pari = cypari2.Pari()

def prpTest(n:int, k:int = 0) -> bool:
    '''
    probable prime test with gmpy2
    (bpsw test + up to k miller-rabin tests)
    production vps timing results
    (2048 bit primes ~0.011sec)
    (3072 bit primes ~0.033sec)
    (4096 bit primes ~0.077sec)
    (6144 bit primes ~0.21sec)
    (8192 bit primes ~0.45sec)
    (12288 bit primes ~1.6sec)
    (16384 bit primes ~3.5sec)
    '''
    assert k >= 0
    # gmp subtracts 24 from 2nd arg and runs up to that many miller-rabin tests
    return gmpy2.is_prime(n,24+k) # type:ignore

def primeTest(n:int) -> bool:
    '''
    provable prime test with pari/gp isprime binding
    use for small numbers that can be tested quickly
    production vps timing results
    (these vary more than prpTest timing and give an idea of typical timing)
    (it seems possible that they may take over 2x as long occasionally)
    (most of the time they take within 0.5x-2x of the times listed below)
    (128 bit primes ~0.01sec)
    (192 bit primes ~0.05sec)
    (256 bit primes ~0.05sec)
    (384 bit primes ~0.2sec)
    (512 bit primes ~0.4sec)
    (768 bit primes ~2sec)
    (1024 bit primes ~2sec) (fails with 8M pari stack, seems fine with 16M)
    '''
    return bool(pari.isprime(n))
