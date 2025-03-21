'''
code for handling things with bases

public interface:
- toBase(base,n) make list of digits (most significant first)
- fromBase(base,digits) reverse the result of toBase()
- toFactorialBase(n) convert to digits (also called factoradic)
- fromFactorialBase(digits) reverse result of toFactorialBase()

all these functions check correctness conditions with assert
'''

def toBase(base:int,n:int,/) -> list[int]:
    ''' convert number to base representation
    (most significant first, 0 is empty list) '''
    assert base >= 2
    assert n >= 0
    ret = []
    while n > 0:
        n,r = divmod(n,base)
        ret.append(r)
    return ret[::-1]

def toFactorialBase(n:int,/) -> list[int]:
    ''' factorial base representation (most significant first, excludes 0) '''
    assert n >= 0
    ret = []
    b = 2
    while n > 0:
        n,r = divmod(n,b)
        b += 1
        ret.append(r)
    return ret[::-1]

def fromBase(base:int,n:list[int],/) -> int:
    ''' convert base representation to integer (most significant first) '''
    assert base >= 2
    n = n[::-1]
    ret = 0
    for i,d in enumerate(n):
        assert 0 <= d < base
        ret += d * base**i
    return ret

def fromFactorialBase(n:list[int],/) -> int:
    ''' convert factorial base representation to integer
    (most significant first, excluding 0) '''
    n = n[::-1]
    ret = 0
    f = 1
    for i,d in enumerate(n):
        assert 0 <= d <= i+1
        f *= i+1
        ret += d * f
    return ret

if __name__ == '__main__':
    # tests

    def check_base(n:int,base:int,digits:list[int]):
        assert toBase(base,n) == digits
        assert fromBase(base,digits) == n

    check_base(0,10,[])
    check_base(123,10,[1,2,3])
    check_base(7109,10,[7,1,0,9])
    check_base(27,2,[1,1,0,1,1])
    check_base(15,3,[1,2,0])
    check_base(0,2,[])
    check_base(1,2,[1])
    check_base(2,2,[1,0])

    def check_factorial_base(n:int,digits:list[int]):
        assert toFactorialBase(n) == digits
        assert fromFactorialBase(digits) == n

    check_factorial_base(0,[])
    check_factorial_base(1,[1])
    check_factorial_base(2,[1,0])
    check_factorial_base(3,[1,1])
    check_factorial_base(4,[2,0])
    check_factorial_base(5,[2,1])
    check_factorial_base(6,[1,0,0])
    check_factorial_base(463,[3,4,1,0,1])
    check_factorial_base(719,[5,4,3,2,1])
    check_factorial_base(720,[1,0,0,0,0,0])
