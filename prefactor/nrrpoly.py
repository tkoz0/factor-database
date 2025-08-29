
from fractions import Fraction
import math
from typing import Iterable

from intpoly import IntPoly

def _basepow(base:int,frac:Fraction) -> int|None:
    # finds p so base**p == frac
    numer,denom = frac.as_integer_ratio()
    if numer <= 0:
        return None
    if numer < denom:
        ret = _basepow(base,1/frac)
        return None if ret is None else -ret
    if denom != 1:
        return None
    basepow_exp,basepow_val = 0,1
    while basepow_val <= numer:
        if basepow_val == numer:
            return basepow_exp
        basepow_exp += 1
        basepow_val *= base
    return None

def _factor(n:int) -> list[int]:
    # fully factors n with trial division
    if n < 2:
        return []
    ret: list[int] = []
    while n % 2 == 0:
        n //= 2
        ret.append(2)
    d = 3
    while d*d <= n:
        while n % d == 0:
            n //= d
            ret.append(d)
        d += 2
    if n != 1:
        ret.append(n)
    return ret

class NrrPoly:
    '''
    the expressions found are polynomials with base^n in place of x
    this class is mostly a wrapper around IntPoly
    the fraction multiple part needs to be stored separately
    this class does not enforce that coefficients have no common factor
    '''
    def __init__(self,base:int,*coefs:int):
        assert 2 <= base <= 36
        self.base = base
        self.poly = IntPoly(*coefs)
        self.coefs = self.poly.coefs

    def degree(self,/) -> int:
        return self.poly.degree()

    def __repr__(self,/) -> str:
        return f'NrrPoly({self.base}{''.join(
            f',{c}' for c in self.poly.coefs)})'

    def __str__(self,/) -> str:
        if self.poly.coefs == ():
            return '0'
        ret = ''
        for i in range(len(self.poly.coefs)-1,-1,-1):
            c = self.poly.coefs[i]
            if c == 0:
                continue
            t = ''
            if i == 0:
                t += str(abs(c))
            else:
                if abs(c) != 1:
                    t += f'{abs(c)}*'
                if i == 1:
                    t += f'{self.base}**n'
                else:
                    t += f'{self.base}**({i}*n)'
            if i == len(self.poly.coefs)-1:
                ret = ['','-'][c < 0] + t
            else:
                ret = f'{ret}{'+-'[c < 0]}{t}'
        return ret

    def latex(self,/) -> str:
        if self.poly.coefs == ():
            return '0'
        ret = ''
        for i in range(len(self.poly.coefs)-1,-1,-1):
            c = self.poly.coefs[i]
            if c == 0:
                continue
            t = ''
            if i == 0:
                t += str(abs(c))
            else:
                if abs(c) != 1:
                    t += f'{abs(c)}\\times'
                if i == 1:
                    t += f'{self.base}^{{n}}'
                else:
                    t += f'{self.base}^{{{i}n}}'
            if i == len(self.poly.coefs)-1:
                ret = ['','-'][c < 0] + t
            else:
                ret = f'{ret}{'+-'[c < 0]}{t}'
        return ret

    def __hash__(self,/) -> int:
        return hash((self.base,self.poly))

    def __bool__(self,/) -> bool:
        return bool(self.poly)

    def __call__(self,n:int,/) -> int:
        # TODO possibly support function composition
        assert n >= 0
        return self.poly(self.base**n)

    def __eq__(self,p,/) -> bool:
        assert isinstance(p,NrrPoly)
        return self.base == p.base and self.poly == p.poly

    def __ne__(self,p,/) -> bool:
        return not (self == p)

    def __pos__(self,/) -> 'NrrPoly':
        return self

    def __neg__(self,/) -> 'NrrPoly':
        return NrrPoly(self.base,*(-self.poly).coefs)

    def __add__(self,p,/) -> 'NrrPoly':
        assert isinstance(p,NrrPoly)
        assert self.base == p.base
        return NrrPoly(self.base,*(self.poly+p.poly).coefs)

    def __sub__(self,p,/) -> 'NrrPoly':
        assert isinstance(p,NrrPoly)
        assert self.base == p.base
        return NrrPoly(self.base,*(self.poly-p.poly).coefs)

    def __mul__(self,p,/) -> 'NrrPoly':
        if isinstance(p,int):
            return NrrPoly(self.base,*(c*p for c in self.coefs))
        assert isinstance(p,NrrPoly)
        assert self.base == p.base
        return NrrPoly(self.base,*(self.poly*p.poly).coefs)

    def __rmul__(self,m,/) -> 'NrrPoly':
        assert isinstance(m,int)
        return NrrPoly(self.base,*(c*m for c in self.coefs))

    def __floordiv__(self,p,/) -> 'NrrPoly':
        return divmod(self,p)[0]

    def __mod__(self,p,/) -> 'NrrPoly':
        return divmod(self,p)[1]

    def __divmod__(self,p,/) -> tuple['NrrPoly','NrrPoly']:
        assert isinstance(p,NrrPoly)
        assert self.base == p.base
        quot,rem = divmod(self.poly,p.poly)
        return NrrPoly(self.base,*quot.coefs),NrrPoly(self.base,*rem.coefs)

    def __pow__(self,p,/) -> 'NrrPoly':
        assert isinstance(p,int)
        assert p >= 0
        return NrrPoly(self.base,*(self.poly**p).coefs)

    def factor(self,/) -> tuple['NrrPoly',...]:
        return tuple(NrrPoly(self.base,*poly.coefs)
                     for poly in self.poly.factor())

    def compareShiftAndMultiply(self,other:'NrrPoly',/) \
            -> None|tuple[Fraction,int]:
        '''
        checks if sequences are identical up to constant multiple and offset
        returns none if they are not, otherwise the multiply and shift

        let f be self and g be the other polynomial
        looks for K,s so f(n) = K * g(n+s) and returns (K,s)

        if a.compareShiftAndMultiply(b) returns (K,s)
        then b.compareShiftAndMultiply(a) returns (1/K,-s)
        '''
        if self.base != other.base or len(self.coefs) != len(other.coefs):
            return None
        # locations of nonzero coefficients must match
        for i in range(len(self.coefs)):
            if self.coefs[i] == 0 and other.coefs[i] != 0:
                return None
            if self.coefs[i] != 0 and other.coefs[i] == 0:
                return None
        # collect nonzero terms, (a,b) means a*base**(b*n)
        left = [(self.coefs[i],i) for i in range(len(self.coefs))
                if self.coefs[i] != 0] # for f(n)
        right = [(other.coefs[i],i) for i in range(len(other.coefs))
                 if other.coefs[i] != 0] # for g(n)
        assert len(left) > 0 and len(right) > 0
        assert len(left) == len(right)
        if len(left) == 1: # same term, multiply and no shift
            return Fraction(left[0][0],right[0][0]),0
        # order terms from largest to smallest
        left = left[::-1]
        right = right[::-1]
        # find offset from first 2 terms
        i,j = left[0][1],left[1][1]
        assert i > j
        p = _basepow(self.base,
                     Fraction(left[0][0]*right[1][0],
                              left[1][0]*right[0][0]))
        if p is None or p % (i-j) != 0:
            return None
        s = p // (i-j)
        # now check that we get the same s for each i,j pair
        for lefti in range(len(left)):
            ai,i = left[lefti]
            bi = right[lefti][0]
            for rightj in range(lefti+1,len(right)):
                bj,j = right[rightj]
                aj = left[rightj][0]
                assert i > j
                p = _basepow(self.base,Fraction(ai*bj,aj*bi))
                if p is None or p % (i-j) != 0 or p // (i-j) != s:
                    return None
        # then determine the multiplier
        i = left[0][1]
        if s < 0:
            K = Fraction(left[0][0]*self.base**(-i*s),
                         right[0][0])
        else:
            K = Fraction(left[0][0],
                         right[0][0]*self.base**(i*s))
        # and be sure each index gets the same result
        for lefti in range(len(left)):
            ai,i = left[lefti]
            bi = right[lefti][0]
            if s < 0:
                K2 = Fraction(ai*self.base**(-i*s),
                              bi)
            else:
                K2 = Fraction(ai,
                              bi*self.base**(i*s))
            if K != K2:
                return None
        return K,s

    def findPeriodicFactors(self,denominator:int,step_range:Iterable[int],/) \
            -> dict[tuple[int,int],tuple[int,...]]:
        '''
        searches for periodic factors that can be found by composing the nrr
        polynomial with a linear polynomial a*n+b
        tries a values in the provided step_range and for each a value, tries
        0 <= b < a
        returns a mapping of (a,b) to the periodic prime factors
        only adds to map if at least 1 prime factor was not found before
        '''
        if self.coefs == ():
            return dict()
        ret: dict[tuple[int,int],tuple[int,...]] = dict()
        found_factors: set[int] = set()
        for a in step_range:
            for b in range(a):
                # check if indexes a*n+b have a common factor (for any n)
                # compose the polynomial with a*n+b in place of n
                # for the ith term with coefficient c, factor out 10^(i*b)
                # then replace 10^(i*a*n) with (10^(i*a*n) - 1) + 1
                # this gives another constant term c*10^(i*b)
                # then factor (10^(i*a) - 1) from (10^(i*a*n) - 1)
                # the result is multiple terms with a known factor of each
                constant_term = sum(c*10**(b*i)
                                    for i,c in enumerate(self.coefs))
                other_terms = [self.coefs[i]*10**(i*b)*(10**(i*a)-1)
                               for i in range(1,len(self.coefs))]
                g = math.gcd(constant_term,*other_terms)
                g,r = divmod(g,denominator)
                assert r == 0
                if g > 1:
                    factors_all = tuple(_factor(g))
                    factors_new = tuple(f for f in factors_all
                                        if f not in found_factors)
                    if factors_new != ():
                        ret[(a,b)] = factors_all
                    for f in factors_new:
                        found_factors.add(f)
                for i in range(10):
                    assert self(a*i+b) % g == 0
        return ret

    def composeLinear(self,a:int,b:int,/) -> 'NrrPoly':
        '''
        composes this nrr polynomial with a linear polynomial a*n+b
        '''
        assert a >= 0 and b >= 0
        ret = NrrPoly(self.base)
        for i,c in enumerate(self.coefs):
            ret += c * self.base**(i*b) * NrrPoly(self.base,0,1)**(a*i)
        for i in range(10):
            assert self(a*i+b) == ret(i)
        return ret

if __name__ == '__main__':
    # NrrPoly testing
    def NP(*coefs:int) -> NrrPoly:
        return NrrPoly(10,*coefs)

    # degree
    assert NP().degree() == 0
    assert NP(5).degree() == 0
    assert NP(1,1).degree() == 1
    assert NP(-1,-1,0).degree() == 1
    assert NP(5,0,0,7).degree() == 3

    # repr
    assert repr(NP()) == 'NrrPoly(10)'
    assert repr(NP(-3)) == 'NrrPoly(10,-3)'
    assert repr(NP(-2,-3,6)) == 'NrrPoly(10,-2,-3,6)'

    # str
    assert str(NP()) == '0'
    assert str(NP(-3)) == '-3'
    assert str(NP(-2,-3,6)) == '6*10**(2*n)-3*10**n-2'
    assert str(NP(7,1,-4,-1)) == '-10**(3*n)-4*10**(2*n)+10**n+7'

    # latex
    assert NP().latex() == '0'
    assert NP(-3).latex() == '-3'
    assert NP(-2,-3,6).latex() == '6\\times10^{2n}-3\\times10^n-2'
    assert NP(7,1,-4,-1).latex() == '-10^{3n}-4\\times10^{2n}+10^n+7'

    # bool
    assert bool(NP()) == False
    assert bool(NP(2)) == True
    assert bool(NP(0,0,3)) == True

    # call
    p = NP()
    assert p(3) == 0
    assert p(0) == 0
    p = NP(5)
    assert p(0) == 5
    assert p(10) == 5
    p = NP(-1,2)
    assert p(0) == 1
    assert p(1) == 19
    assert p(2) == 199
    assert p(5) == 199999
    p = NP(7,0,3)
    assert p(0) == 10
    assert p(1) == 307
    assert p(3) == 3000007
    assert p(6) == 3000000000007

    # eq and ne
    assert NP() == NP()
    assert NP() != NP(-3)
    assert NP(1,2,3,0,0,0) == NP(1,2,3)
    assert NP(5,4,3,2) != NP(5,3,4,2)

    # pos and neg
    assert +NP() == NP()
    assert +NP(4) == NP(4)
    assert +NP(1,-1) == NP(1,-1)
    assert +NP(0,0,0,1) == NP(0,0,0,1)
    assert -NP() == NP()
    assert -NP(9) == NP(-9)
    assert -NP(2,-2) == NP(-2,2)
    assert -NP(3,0,-2,0,4) == NP(-3,0,2,0,-4)

    # add and sub
    assert NP() + NP() == NP()
    assert NP(3) + NP(-1,1) == NP(2,1)
    assert NP(-7,0,1) + NP(3,0,-1) == NP(-4)
    assert NP(0,0,0,1) + NP(-1,0,2) == NP(-1,0,2,1)
    assert NP() - NP() == NP()
    assert NP(4,7) - NP(6,3) == NP(-2,4)
    assert NP(0,0,0,1) - NP(0,0,1) == NP(0,0,-1,1)
    assert NP(5,1,4) - NP(5,-1,4) == NP(0,2)

    # mul
    assert NP() * NP() == NP()
    assert NP(3) * NP(6) == NP(18)
    assert NP(5) * NP(-2,1) == NP(-10,5)
    assert NP(-1,2) * NP(-2,1) == NP(2,-5,2)
    assert NP(0,1) * NP(0,0,1) == NP(0,0,0,1)
    assert NP(7,-5,3) * NP(-8,6,4) == NP(-56,82,-26,-2,12)

    # div and mod
    p1 = NP(-8,12)
    p2 = NP(4)
    assert p1 // p2 == NP(-2,3)
    assert p1 % p2 == NP()
    assert divmod(p1,p2) == (NP(-2,3),NP())
    p1 = NP(15,8,-4)
    assert p1 // p2 == NP(3,2,-1)
    assert p1 % p2 == NP(3)
    assert divmod(p1,p2) == (NP(3,2,-1),NP(3))
    p3 = NP(-56,82,-26,-2,12)
    assert divmod(p3,NP(7,-5,3)) == (NP(-8,6,4),NP())
    assert divmod(p3,NP(-8,6,4)) == (NP(7,-5,3),NP())
    p3 += NP(56,-82)
    assert divmod(p3,NP(7,-5,3)) == (NP(-8,6,4),NP(56,-82))
    assert divmod(p3,NP(-8,6,4)) == (NP(7,-5,3),NP(56,-82))
    p3 -= NP(112,-164)
    assert divmod(p3,NP(7,-5,3)) == (NP(-8,6,4),NP(-56,82))
    assert divmod(p3,NP(-8,6,4)) == (NP(7,-5,3),NP(-56,82))
    p1 = NP(-1,2)
    p2 = NP(-1,3)
    p3 = NP(-1,-1,1)
    assert NP(-1,4,0,-11,6) // p1 // p2 == p3
    p1 = NP(2,4,7)
    p2 = NP(1,2,3)
    assert divmod(p1,p2) == (NP(2),NP(0,0,1))

    # pow
    assert NP(4)**4 == NP(256)
    assert NP(-1,1)**3 == NP(-1,3,-3,1)
    assert NP(4,3,1)**2 == NP(16,24,17,6,1)
    assert NP(8,4,2,1)**0 == NP(1)

    # factor
    # factorable base 10 near repdigit related patterns
    ftests = (
        (10,- 9,-1,1,-1,10, 1), # 11011
        (10,  9,-1,1, 1,10,-1), # 11211
        (10,- 3,-1,2,-1, 5, 1), # 33233
        (10,  3,-1,2, 1, 5,-1), # 33433
        (40,-27,-4,5,-4, 8, 1), # 44144
        (40, 27,-4,5, 4, 8,-1), # 44744
        (20,- 3,-2,4, 1, 5,-2), # 66566
        (20,  3,-2,4,-1, 5, 2), # 66766
    )
    for a,b,c,f1a,f1b,f2a,f2b in ftests:
        # polynomial factorization should be independent of base
        for base in range(2,36+1):
            nrr = NrrPoly(base,c,b,a)
            fs = nrr.factor()
            assert len(fs) == 3
            f0,f1,f2 = fs
            assert f0 == NrrPoly(base,1)
            assert f1 == NrrPoly(base,f1b,f1a)
            assert f2 == NrrPoly(base,f2b,f2a)
