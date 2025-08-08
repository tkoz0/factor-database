
from intpoly import IntPoly

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
                    t += f'{self.base}^n'
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
        assert isinstance(p,NrrPoly)
        assert self.base == p.base
        return NrrPoly(self.base,*(self.poly*p.poly).coefs)

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
