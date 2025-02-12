'''
code for number sequences
'''

from typing import Callable

from primes import nthPrime,nthComposite

# returns a constant linear recursive sequence function (without cache)
# init = first d terms (f(0),f(1),...,f(d-1))
# recur = (c_d,c_{d-1},...,c_1) meaning
#         f(n) = c_1*f(n-1) + c_2*f(n-2) + ... + c_d*f(n-d)
def _const_recur_linear_nocache(start:tuple[int,...],
                                recur:tuple[int,...]) \
                            -> Callable[[int],int]:
    assert len(start) == len(recur)
    def seq(n:int) -> int:
        if n < len(start):
            return start[n]
        prev = start
        for _ in range(n+1-len(start)):
            prev = (*(prev[1:]),
                    sum(c*prev[i] for i,c in enumerate(recur)))
        return prev[-1]
    return seq

# returns a constant linear recursive sequence function
# cached sequentially from start
# init = first d terms (f(0),f(1),...,f(d-1))
# recur = (c_1,c_2,...,c_d) meaning
#         f(n) = c_1*f(n-1) + c_2*f(n-2) + ... + c_d*f(n-d)
def _const_recur_linear_cache(start:tuple[int,...],
                              recur:tuple[int,...]) \
                            -> Callable[[int],int]:
    assert len(start) == len(recur)
    d = len(recur)
    cache: list[int] = list(start)
    def seq(n:int) -> int:
        while len(cache) <= n:
            #print(f'generating index {len(cache)}')
            cache.append(sum(c*cache[-d+i] for i,c in enumerate(recur)))
        return cache[n]
    return seq

fibonacci = _const_recur_linear_cache((0,1),(1,1))

lucas = _const_recur_linear_cache((2,1),(1,1))

padovan = _const_recur_linear_cache((1,1,1),(1,1,0))

perrin = _const_recur_linear_cache((3,0,2),(1,1,0))

# offset of padovan
vanderlaan = _const_recur_linear_cache((1,0,1),(1,1,0))

# not to be confused with narayana numbers
narayana = _const_recur_linear_cache((1,1,1),(1,0,1))

# U(1,-2)
jacobsthal = _const_recur_linear_cache((0,1),(2,1))

# V(1,-2)
jacobsthal_lucas = _const_recur_linear_cache((2,1),(2,1))

# U(2,-1)
pell = _const_recur_linear_cache((0,1),(1,2))

# V(2,-1)
pell_lucas = _const_recur_linear_cache((2,2),(1,2))

def _make_lucas_u(p:int,q:int) -> Callable[[int],int]:
    return _const_recur_linear_cache((0,1),(-q,p))

def _make_lucas_v(p:int,q:int) -> Callable[[int],int]:
    return _const_recur_linear_cache((2,p),(-q,p))

_cache_lu: dict[tuple[int,int],Callable[[int],int]] = dict()
_cache_lv: dict[tuple[int,int],Callable[[int],int]] = dict()

def lucas_u(p:int,q:int,n:int) -> int:
    '''
    generic lucas U sequence function with result caching
    '''
    global _cache_lu
    if (p,q) not in _cache_lu:
        _cache_lu[(p,q)] = _make_lucas_u(p,q)
    return _cache_lu[(p,q)](n)

def lucas_v(p:int,q:int,n:int) -> int:
    '''
    generic lucas V sequence function with result caching
    '''
    global _cache_lv
    if (p,q) not in _cache_lv:
        _cache_lv[(p,q)] = _make_lucas_v(p,q)
    return _cache_lv[(p,q)](n)

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
    i = 1
    while nthPrime(i) <= n:
        ret *= nthPrime(i)
        i += 1
    return ret

def compositorial(n:int) -> int:
    assert n > 0
    ret = 1
    i = 1
    while nthComposite(i) <= n:
        ret *= nthComposite(i)
        i += 1
    return ret

def repunit(base:int,index:int) -> int:
    assert base >= 2
    assert index >= 0
    ret = (base**index - 1) // (base-1)
    return ret

if __name__ == '__main__':
    # tests

    assert [fibonacci(n) for n in range(15)] \
        == [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377]
    assert [lucas(n) for n in range(15)] \
        == [2,1,3,4,7,11,18,29,47,76,123,199,322,521,843]
    assert [padovan(n) for n in range(20)] \
        == [1,1,1,2,2,3,4,5,7,9,12,16,21,28,37,49,65,86,114,151]
    assert [perrin(n) for n in range(18)] \
        == [3,0,2,3,2,5,5,7,10,12,17,22,29,39,51,68,90,119]
    assert [vanderlaan(n) for n in range(20)] \
        == [1,0,1,1,1,2,2,3,4,5,7,9,12,16,21,28,37,49,65,86]
    assert [narayana(n) for n in range(14)] \
        == [1,1,1,2,3,4,6,9,13,19,28,41,60,88]
    assert [jacobsthal(n) for n in range(15)] \
        == [0,1,1,3,5,11,21,43,85,171,341,683,1365,2731,5461]
    assert [jacobsthal_lucas(n) for n in range(14)] \
        == [2,1,5,7,17,31,65,127,257,511,1025,2047,4097,8191]
    assert [pell(n) for n in range(13)] \
        == [0,1,2,5,12,29,70,169,408,985,2378,5741,13860]
    assert [pell_lucas(n) for n in range(11)] \
        == [2,2,6,14,34,82,198,478,1154,2786,6726]

    assert all(lucas_u(1,-1,n) == fibonacci(n) for n in range(100))
    assert all(lucas_v(1,-1,n) == lucas(n) for n in range(100))
    assert all(lucas_u(2,-1,n) == pell(n) for n in range(100))
    assert all(lucas_v(2,-1,n) == pell_lucas(n) for n in range(100))
    assert all(lucas_u(1,-2,n) == jacobsthal(n) for n in range(100))
    assert all(lucas_v(1,-2,n) == jacobsthal_lucas(n) for n in range(100))
    assert all(lucas_u(3,2,n) == 2**n-1 for n in range(100))
    assert all(lucas_v(3,2,n) == 2**n+1 for n in range(100))

    # repunit in a few bases
    for x in range(2,37):
        assert all(lucas_u(x+1,x,n) == (x**n-1)//(x-1) for n in range(100))
        assert all(lucas_v(x+1,x,n) == x**n+1 for n in range(100))

    assert [factorial(n) for n in range(10)] \
        == [1,1,2,6,24,120,720,5040,40320,362880]
    assert [primorial(n) for n in range(1,13)] \
        == [1,2,6,6,30,30,210,210,210,210,2310,2310]
    assert [compositorial(n) for n in range(1,12)] \
        == [1,1,1,4,4,24,24,192,1728,17280,17280]
    assert [repunit(2,n) for n in range(10)] \
        == [0,1,3,7,15,31,63,127,255,511]
    assert [repunit(10,n) for n in range(10)] \
        == [0,1,11,111,1111,11111,111111,1111111,11111111,111111111]
