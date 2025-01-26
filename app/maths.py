import gmpy2
import cypari2
pari = cypari2.Pari()

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
