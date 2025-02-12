import bases
import primes
import sequences

def expreval(expr:str,n:int) -> int:
    ret = eval(expr.replace('{}','n'),{
        'bases': bases,
        'primes': primes,
        'sequences': sequences,
        'n': n
    })
    assert isinstance(ret,int)
    return ret
