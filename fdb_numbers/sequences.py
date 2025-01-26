'''
code for number sequences
'''

from fdb_numbers.primes import primeSieve

def fibonacci(n:int) -> int:
    # f(0)=0,f(1)=1,f(n)=f(n-1)+f(n-2)
    assert n >= 0
    if n == 0:
        return 0
    if n == 1:
        return 1
    a,b = 0,1
    for _ in range(n-1):
        a,b = b,a+b
    return b

def lucas(n:int) -> int:
    # f(0)=2,f(1)=1,f(n)=f(n-1)+f(n-2)
    assert n >= 0
    if n == 0:
        return 2
    if n == 1:
        return 1
    a,b = 2,1
    for _ in range(n-1):
        a,b = b,a+b
    return b

def factorial(n:int) -> int:
    assert n >= 0
    if n == 0:
        return 1
    ret = 1
    for i in range(1,n+1):
        ret *= i
    return ret

def primorial(n:int) -> int:
    assert n > 0
    ret = 1
    for p in primeSieve(n+1):
        ret *= p
    return ret

def compositorial(n:int) -> int:
    assert n > 0
    primes = set(primeSieve(n+1))
    ret = 1
    for c in range(1,n+1):
        if c not in primes:
            ret *= c
    return ret

def repunit(base:int,index:int) -> int:
    assert base >= 2
    assert index >= 0
    ret = (base**index - 1) // (base-1)
    return ret

def padovan(n:int) -> int:
    # f(0)=f(1)=f(2)=1,f(n)=f(n-2)+f(n-3)
    # also satisfies f(n)=f(n-1)+f(n-5)
    assert n >= 0
    if n in (0,1,2):
        return 1
    a,b,c = 1,1,1
    for _ in range(n-2):
        a,b,c = b,c,a+b
    return c

def perrin(n:int) -> int:
    # f(0)=3,f(1)=0,f(2)=2,f(n)=f(n-2)+f(n-3)
    assert n >= 0
    if n == 0:
        return 3
    if n == 1:
        return 0
    if n == 2:
        return 2
    a,b,c = 3,0,2
    for _ in range(n-2):
        a,b,c = b,c,a+b
    return c

def vanderlaan(n:int) -> int:
    # f(0)=1,f(1)=0,f(2)=1,f(n)=f(n-2)+f(n-3)
    # offset of padovan
    assert n >= 0
    if n == 0:
        return 1
    if n == 1:
        return 0
    if n == 2:
        return 1
    a,b,c = 1,0,1
    for _ in range(n-2):
        a,b,c = b,c,a+b
    return c

def narayana(n:int) -> int:
    # f(0)=f(1)=f(2)=1,f(n)=f(n-1)+f(n-3)
    # not to be confused with narayana numbers (from combinatorics)
    assert n >= 0
    if n in (0,1,2):
        return 1
    a,b,c = 1,1,1
    for _ in range(n-2):
        a,b,c = b,c,a+c
    return c

if __name__ == '__main__':
    # tests

    assert [fibonacci(n) for n in range(15)] \
        == [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377]
    assert [lucas(n) for n in range(15)] \
        == [2,1,3,4,7,11,18,29,47,76,123,199,322,521,843]
    assert [factorial(n) for n in range(10)] \
        == [1,1,2,6,24,120,720,5040,40320,362880]
    assert [primorial(n) for n in range(1,13)] \
        == [1,2,6,6,30,30,210,210,210,210,2310,2310]
    assert [compositorial(n) for n in range(1,12)] \
        == [1,1,1,4,4,24,24,192,1728,17280,17280]
    assert [repunit(2,n) for n in range(10)] \
        == [0,1,3,7,15,31,63,127,255,511]
    assert [padovan(n) for n in range(20)] \
        == [1,1,1,2,2,3,4,5,7,9,12,16,21,28,37,49,65,86,114,151]
    assert [perrin(n) for n in range(18)] \
        == [3,0,2,3,2,5,5,7,10,12,17,22,29,39,51,68,90,119]
    assert [vanderlaan(n) for n in range(20)] \
        == [1,0,1,1,1,2,2,3,4,5,7,9,12,16,21,28,37,49,65,86]
    assert [narayana(n) for n in range(14)] \
        == [1,1,1,2,3,4,6,9,13,19,28,41,60,88]
