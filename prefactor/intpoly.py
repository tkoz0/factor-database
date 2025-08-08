
import itertools
import math

def _divisors(n:int) -> list[int]:
    # basic up to square root algorithm for divisors
    n = abs(n)
    assert n > 0
    i = 1
    lo: list[int] = []
    hi: list[int] = []
    while i*i < n:
        if n % i == 0:
            lo.append(i)
            hi.append(n//i)
        i += 1
    if i*i == n:
        lo.append(i)
    return lo + hi[::-1]

class IntPoly:
    '''
    represents polynomials of integer coefficients
    only allows operations which maintain integrality
    '''
    def __init__(self,*coefs:int):
        # leading term should be nonzero
        while len(coefs) > 0 and coefs[-1] == 0:
            coefs = coefs[:-1]
        self.coefs = coefs

    def degree(self,/) -> int:
        return 0 if self.coefs == () else len(self.coefs) - 1

    def __repr__(self,/) -> str:
        return f'IntPoly({','.join(str(c) for c in self.coefs)})'

    def __str__(self,/) -> str:
        if self.coefs == ():
            return '0'
        ret = ''
        for i in range(len(self.coefs)-1,-1,-1):
            c = self.coefs[i]
            if c == 0:
                continue
            t = ''
            if i == 0:
                t += str(abs(c))
            else:
                if abs(c) != 1:
                    t += f'{abs(c)}*'
                if i == 1:
                    t += f'x'
                else:
                    t += f'x**{i}'
            if i == len(self.coefs)-1:
                ret = ['','-'][c < 0] + t
            else:
                ret = f'{ret}{'+-'[c < 0]}{t}'
        return ret

    def latex(self,/) -> str:
        if self.coefs == ():
            return '0'
        ret = ''
        for i in range(len(self.coefs)-1,-1,-1):
            c = self.coefs[i]
            if c == 0:
                continue
            t = ''
            if i == 0:
                t += str(abs(c))
            else:
                if abs(c) != 1:
                    t += f'{abs(c)}'
                if i == 1:
                    t += f'x'
                elif i < 10:
                    t += f'x^{i}'
                else:
                    t += f'x^{{{i}}}'
            if i == len(self.coefs)-1:
                ret = ['','-'][c < 0] + t
            else:
                ret = f'{ret}{'+-'[c < 0]}{t}'
        return ret

    def __hash__(self,/) -> int:
        return hash(self.coefs)

    def __bool__(self,/) -> bool:
        return bool(self.coefs)

    def __call__(self,n:int,/) -> int:
        # TODO maybe support function composition
        assert n >= 0
        ret = 0
        n_pow = 1
        for c in self.coefs:
            ret += c * n_pow
            n_pow *= n
        return ret

    def __eq__(self,p,/) -> bool:
        assert isinstance(p,IntPoly)
        return self.coefs == p.coefs

    def __ne__(self,p,/) -> bool:
        return not (self == p)

    def __pos__(self,/) -> 'IntPoly':
        return self

    def __neg__(self,/) -> 'IntPoly':
        return IntPoly(*(-c for c in self.coefs))

    def __add__(self,p,/) -> 'IntPoly':
        assert isinstance(p,IntPoly)
        m = max(len(self.coefs),len(p.coefs))
        cs1 = self.coefs + (0,) * (m - len(self.coefs))
        cs2 = p.coefs + (0,) * (m - len(p.coefs))
        return IntPoly(*map(lambda x,y: x + y, cs1, cs2))

    def __sub__(self,p,/) -> 'IntPoly':
        assert isinstance(p,IntPoly)
        m = max(len(self.coefs),len(p.coefs))
        cs1 = self.coefs + (0,) * (m - len(self.coefs))
        cs2 = p.coefs + (0,) * (m - len(p.coefs))
        return IntPoly(*map(lambda x,y: x - y, cs1, cs2))

    def __mul__(self,p,/) -> 'IntPoly':
        assert isinstance(p,IntPoly)
        if self.coefs == () or p.coefs == ():
            return IntPoly()
        ret = [0] * (len(self.coefs) + len(p.coefs) - 1)
        for i in range(len(self.coefs)):
            for j in range(len(p.coefs)):
                ret[i+j] += self.coefs[i] * p.coefs[j]
        return IntPoly(*ret)

    def __floordiv__(self,p,/) -> 'IntPoly':
        return divmod(self,p)[0]

    def __mod__(self,p,/) -> 'IntPoly':
        return divmod(self,p)[1]

    def __divmod__(self,p,/) -> tuple['IntPoly','IntPoly']:
        debug = False
        assert isinstance(p,IntPoly)
        if debug:
            print(f'dividing {self} / {p}')
        assert p.coefs != ()
        if self.coefs == ():
            return IntPoly(),IntPoly()
        quot = [0] * (len(self.coefs) - len(p.coefs) + 1)
        rem = [self.coefs[i] for i in range(len(quot),len(self.coefs))] + [0]
        if debug:
            print('start',quot)
            print('start',rem)
        assert len(rem) == len(p.coefs)
        i = len(quot) - 1
        while i >= 0:
            assert rem[-1] == 0
            rem = [self.coefs[i]] + rem[:-1]
            quot[i],r = divmod(rem[-1],p.coefs[-1]) # type:ignore
            # allow last term to be same degree as divisor
            assert i == 0 or r == 0
            for j in range(len(rem)):
                rem[j] -= quot[i] * p.coefs[j]
            if debug:
                print(i,quot)
                print(i,rem)
            i -= 1
        quot = IntPoly(*quot)
        rem = IntPoly(*rem)
        if debug:
            print(f'quot = {quot}, rem = {rem}')
        assert quot*p + rem == self
        return quot,rem

    def __pow__(self,p,/) -> 'IntPoly':
        assert isinstance(p,int)
        assert p >= 0
        ret = IntPoly(1)
        poly = self
        while p > 0:
            if p % 2 == 1:
                ret *= poly
            poly *= poly
            p //= 2
        return ret

    def derivative(self) -> 'IntPoly':
        if self.coefs == ():
            return IntPoly()
        return IntPoly(*(i * self.coefs[i]
                         for i in range(1,len(self.coefs))))

    def integral(self,c:int=0) -> 'IntPoly':
        for i in range(len(self.coefs)):
            assert self.coefs[i] % (i+1) == 0
        return IntPoly(c,*(self.coefs[i] // (i+1)
                           for i in range(len(self.coefs))))

    def factor(self) -> tuple['IntPoly',...]:
        debug = False
        if debug:
            print(f'factoring {self}')
        if self.coefs == ():
            return ()
        ret_factors: list[IntPoly] = []
        # remove common factor
        g = math.gcd(*self.coefs)
        if self.coefs[-1] < 0: # type:ignore
            g = -g
        ret_factors.append(IntPoly(g))
        poly = IntPoly(*(c // g for c in self.coefs))
        if debug:
            print(f'remove factors: {poly}')
        # divide out x
        while poly.coefs[0] == 0: # type:ignore
            ret_factors.append(IntPoly(0,1))
            poly //= IntPoly(0,1)
            if debug:
                print(f'divide x: {poly}')
        while True:
            if poly.degree() == 0: # constant
                assert poly == IntPoly(1)
                break
            elif poly.degree() == 1: # linear
                ret_factors.append(poly)
                break
            else: # quadratic or higher, try to find linear factors
                # factor p(x)=q(x)r(x) where p(x) degree n >= 2 and q(x)=a*x+b
                # a divides p{n} and b divides p{0}
                factored = False
                hi_divs = _divisors(poly.coefs[-1]) # type:ignore
                lo_divs = _divisors(poly.coefs[0]) # type:ignore
                for a,b in itertools.product(hi_divs,lo_divs):
                    try: # a*x + b
                        if debug:
                            print(f'trying {IntPoly(b,a)}')
                        quot,rem = divmod(poly,IntPoly(b,a))
                        if rem == IntPoly():
                            ret_factors.append(IntPoly(b,a))
                            poly = quot
                            factored = True
                            break
                    except:
                        pass
                    try: # a*x - b
                        if debug:
                            print(f'trying {IntPoly(-b,a)}')
                        quot,rem = divmod(poly,IntPoly(-b,a))
                        if rem == IntPoly():
                            ret_factors.append(IntPoly(-b,a))
                            poly = quot
                            factored = True
                            break
                    except:
                        pass
                if poly.degree() >= 4 and not factored:
                    # also try to find quadratic factors
                    # factor p(x)=q(x)r(x) where p(x) degree n >= 4
                    # and q(x)=a*x^2+b*x+c
                    pnorm2 = 1 + math.isqrt(sum(c*c for c in poly.coefs))
                    bound: int = 2**(poly.degree()-2) * pnorm2
                    # leading p coefficients
                    pn = poly.coefs[-1] # type:ignore
                    pnm1 = poly.coefs[-2] # type:ignore
                    lo_divs_pm: list[int] = []
                    for d in lo_divs:
                        lo_divs_pm.append(d)
                        lo_divs_pm.append(-d)
                    for a,c in itertools.product(hi_divs,lo_divs_pm):
                        if factored:
                            break
                        # b = a*(p{n-1} - a*r{n-3}) / p{n}
                        # supposedly conservative use of margotte's bound
                        bb1 = abs(a*pnm1 // pn)
                        bb2 = abs(a*a // pn)
                        b_bound = (1 + bb1) + (1 + bb2) * bound
                        if debug:
                            print(f'trying a = {a}, c = {c} '
                                  f'with b in [-{b_bound},{b_bound}]')
                        # loop on the r{n-3} coefficient
                        r = 0
                        while True:
                            b1,dr1 = divmod(a*pnm1 - a*a*r, pn)
                            b2,dr2 = divmod(a*pnm1 + a*a*r, pn)
                            if abs(b1) > b_bound and abs(b2) > b_bound:
                                break
                            if dr1 == 0: # a*x^2+b1*x+c
                                try:
                                    quot,rem = divmod(poly,IntPoly(c,b1,a))
                                    if rem == IntPoly():
                                        ret_factors.append(IntPoly(c,b1,a))
                                        poly = quot
                                        factored = True
                                        break
                                except:
                                    pass
                            if dr2 == 0: # a*x^2-b1*x+c
                                try:
                                    quot,rem = divmod(poly,IntPoly(c,b2,a))
                                    if rem == IntPoly():
                                        ret_factors.append(IntPoly(c,b2,a))
                                        poly = quot
                                        factored = True
                                        break
                                except:
                                    pass
                            r += 1
                if not factored:
                    ret_factors.append(poly)
                    break
        return tuple(ret_factors)

if __name__ == '__main__':
    IP = IntPoly

    # degree
    assert IP().degree() == 0
    assert IP(5).degree() == 0
    assert IP(1,1).degree() == 1
    assert IP(-1,-1,0).degree() == 1
    assert IP(5,0,0,7).degree() == 3

    # repr
    assert repr(IP()) == 'IntPoly()'
    assert repr(IP(-3)) == 'IntPoly(-3)'
    assert repr(IP(-2,-3,6)) == 'IntPoly(-2,-3,6)'

    # str
    assert str(IP()) == '0'
    assert str(IP(-3)) == '-3'
    assert str(IP(-2,-3,6)) == '6*x**2-3*x-2'
    assert str(IP(7,1,-4,-1)) == '-x**3-4*x**2+x+7'

    # latex
    assert IP().latex() == '0'
    assert IP(-3).latex() == '-3'
    assert IP(-2,-3,6).latex() == '6x^2-3x-2'
    assert IP(7,1,-4,-1).latex() == '-x^3-4x^2+x+7'

    # bool
    assert bool(IP()) == False
    assert bool(IP(2)) == True
    assert bool(IP(0,0,3)) == True

    # call
    p = IP()
    assert p(3) == 0
    assert p(0) == 0
    p = IP(5)
    assert p(0) == 5
    assert p(10) == 5
    p = IP(-1,2)
    assert p(0) == -1
    assert p(1) == 1
    assert p(2) == 3
    assert p(5) == 9
    p = IP(7,0,3)
    assert p(0) == 7
    assert p(1) == 10
    assert p(3) == 34
    assert p(6) == 115

    # eq and ne
    assert IP() == IP()
    assert IP() != IP(-3)
    assert IP(1,2,3,0,0,0) == IP(1,2,3)
    assert IP(5,4,3,2) != IP(5,3,4,2)

    # pos and neg
    assert +IP() == IP()
    assert +IP(4) == IP(4)
    assert +IP(1,-1) == IP(1,-1)
    assert +IP(0,0,0,1) == IP(0,0,0,1)
    assert -IP() == IP()
    assert -IP(9) == IP(-9)
    assert -IP(2,-2) == IP(-2,2)
    assert -IP(3,0,-2,0,4) == IP(-3,0,2,0,-4)

    # add and sub
    assert IP() + IP() == IP()
    assert IP(3) + IP(-1,1) == IP(2,1)
    assert IP(-7,0,1) + IP(3,0,-1) == IP(-4)
    assert IP(0,0,0,1) + IP(-1,0,2) == IP(-1,0,2,1)
    assert IP() - IP() == IP()
    assert IP(4,7) - IP(6,3) == IP(-2,4)
    assert IP(0,0,0,1) - IP(0,0,1) == IP(0,0,-1,1)
    assert IP(5,1,4) - IP(5,-1,4) == IP(0,2)

    # mul
    assert IP() * IP() == IP()
    assert IP(3) * IP(6) == IP(18)
    assert IP(5) * IP(-2,1) == IP(-10,5)
    assert IP(-1,2) * IP(-2,1) == IP(2,-5,2)
    assert IP(0,1) * IP(0,0,1) == IP(0,0,0,1)
    assert IP(7,-5,3) * IP(-8,6,4) == IP(-56,82,-26,-2,12)

    # div and mod
    p1 = IP(-8,12)
    p2 = IP(4)
    assert p1 // p2 == IP(-2,3)
    assert p1 % p2 == IP()
    assert divmod(p1,p2) == (IP(-2,3),IP())
    p1 = IP(15,8,-4)
    assert p1 // p2 == IP(3,2,-1)
    assert p1 % p2 == IP(3)
    assert divmod(p1,p2) == (IP(3,2,-1),IP(3))
    p3 = IP(-56,82,-26,-2,12)
    assert divmod(p3,IP(7,-5,3)) == (IP(-8,6,4),IP())
    assert divmod(p3,IP(-8,6,4)) == (IP(7,-5,3),IP())
    p3 += IP(56,-82)
    assert divmod(p3,IP(7,-5,3)) == (IP(-8,6,4),IP(56,-82))
    assert divmod(p3,IP(-8,6,4)) == (IP(7,-5,3),IP(56,-82))
    p3 -= IP(112,-164)
    assert divmod(p3,IP(7,-5,3)) == (IP(-8,6,4),IP(-56,82))
    assert divmod(p3,IP(-8,6,4)) == (IP(7,-5,3),IP(-56,82))
    p1 = IP(-1,2)
    p2 = IP(-1,3)
    p3 = IP(-1,-1,1)
    assert IP(-1,4,0,-11,6) // p1 // p2 == p3
    p1 = IP(2,4,7)
    p2 = IP(1,2,3)
    assert divmod(p1,p2) == (IP(2),IP(0,0,1))

    # pow
    assert IP(4)**4 == IP(256)
    assert IP(-1,1)**3 == IP(-1,3,-3,1)
    assert IP(4,3,1)**2 == IP(16,24,17,6,1)
    assert IP(8,4,2,1)**0 == IP(1)
    assert IP(2,2)**6 == IP(64) * IP(1,6,15,20,15,6,1)

    # derivative
    assert IP().derivative() == IP()
    assert IP(7).derivative() == IP()
    assert IP(6,-6,12,-4).derivative() == IP(-6,24,-12)
    assert IP(0,0,0,3,5).derivative() == IP(0,0,9,20)

    # integral
    assert IP().integral() == IP()
    assert IP(-2).integral(-3) == IP(-3,-2)
    assert IP(6,-6,12,-4).integral() == IP(0,6,-3,4,-1)
    assert IP(0,0,0,8,20).integral(6) == IP(6,0,0,0,2,4)

    # factor
    assert IP().factor() == ()
    assert IP(-21).factor() == (IP(-21),)
    assert IP(0,1).factor() == (IP(1),IP(0,1))
    assert IP(-6,3).factor() == (IP(3),IP(-2,1))
    assert IP(-1,-1,1).factor() == (IP(1),IP(-1,-1,1))
    assert IP(-1,0,1).factor() == (IP(1),IP(1,1),IP(-1,1))
    assert IP(1,0,-1).factor() == (IP(-1),IP(1,1),IP(-1,1))
    assert IP(63,23,2).factor() == (IP(1),IP(7,1),IP(9,2))
    assert IP(-1,4,0,-11,6).factor() == (IP(1),IP(-1,2),IP(-1,3),IP(-1,-1,1))
    assert IP(-56,82,-26,-2,12).factor() == (IP(2),IP(-4,3,2),IP(7,-5,3))
    assert IP(-1,-1,5,4,0,5).factor() == (IP(1),IP(-1,0,5),IP(1,1,0,1))
    assert IP(-1,-1,0,0,0,1).factor() == (IP(1),IP(-1,-1,0,0,0,1))
    # this last one takes a while but is a more rigorous quadratic factor test
    #assert IP(-630,1390,260,-1230,-60,180).factor() \
    #    == (IP(10),IP(-7,10,6),IP(9,-7,-6,3))
