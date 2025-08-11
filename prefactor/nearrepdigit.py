'''
near repdigit related (nrr) number sequence analysis
deduplicate sequences by multiplier and index shift
initially meant to check sequence "uniqueness" on stdkmd.net/nrr
stdkmd.net/nrr has 601 nrr sequences as of writing this
603 if the special 11111 and 10001 are counted (different table formats)
the missing number patterns are identified to be these (decomposable):
(the + indicates sequence offsets)
11011 = [10001+1][11111+0]
11211 = [11111+2][10001+0]
33233 = [16667+0][19999+1]
33433 = [49999+1][66667+0]
44144 = [88889+0][49996+0]
44744 = [79999+1][55556+0]
66566 = [50002+0][13333+1]
66766 = [16666+1][40001+0]
'''

from fractions import Fraction
import math
import re

from nrrpoly import NrrPoly

def _regexToStdkmd(s:str,/) -> str:
    # regex to the 5 digit pattern format used on stdkmd.net
    if re.fullmatch(r'[^\*]\*',s): # AAAAA
        return 5*s[0]
    elif re.fullmatch(r'[^\*]\*[^\*]',s): # AAAAB
        return 4*s[0]+s[2]
    elif re.fullmatch(r'[^\*][^\*]\*',s): # ABBBB
        return s[0]+4*s[1]
    elif re.fullmatch(r'[^\*]\*[^\*][^\*]',s): # AAABA
        return 3*s[0]+s[2]+s[3]
    elif re.fullmatch(r'[^\*][^\*][^\*]\*',s): # ABAAA
        return s[0]+s[1]+3*s[2]
    elif re.fullmatch(r'[^\*][^\*]\*[^\*]',s): # ABBBA or ABBBC
        return s[0]+3*s[1]+s[3]
    elif re.fullmatch(r'[^\*]\*[^\*][^\*]\*',s): # AABAA
        return 2*s[0]+s[2]+2*s[3]
    else:
        return f'other({s})'

def _rep(d,/):
    return f'{d}{d}..{d}{d}'

class NrrPattern:
    '''
    near repdigit related number pattern
    bases supported are 2-36 using digits 0-9 then a-z
    if d is any digit, then pattern is a string of "d" and "d*"
    "d" means a single digit
    "d*" means 0 or more repeated digits
    example: "12*3" produces the sequence 13,123,1223,12223,...
    '''

    def __init__(self,base:int,pattern:str,sort_tag:int=0,/):
        assert 2 <= base <= 36
        digits_str = '0123456789abcdefghijklmnopqrstuvwxyz'
        self.base = base
        self.sort_tag = sort_tag

        # pattern parsing loop
        found_first_digit = False
        pattern_num: list[int] = []
        pattern_rep: list[bool] = []
        regex_str = ''
        disp_str = ''
        leading_digit = None
        trailing_digit = None
        for i in range(len(pattern)):
            if pattern[i] == '*':
                continue
            d = digits_str.find(pattern[i])
            assert d != -1, 'invalid digit'
            assert d < base, 'digit too large for base'
            #d_start = '10'[found_first_digit]
            #d_re = f'[{d_start}-{d}]' if d < 10 \
            #    else f'[{d_start}-9a-{'abcdefghijklmnopqrstuvwxyz'[d-10]}]'
            if not found_first_digit:
                found_first_digit = True
                assert d != 0, 'pattern cannot start with zero'
                leading_digit = d
            trailing_digit = d
            pattern_num.append(d)
            if i+1 < len(pattern) and pattern[i+1] == '*':
                pattern_rep.append(True)
                regex_str += f'{pattern[i]}*'
                disp_str += _rep(pattern[i])
            else:
                pattern_rep.append(False)
                regex_str += pattern[i]
                disp_str += pattern[i]
            found_first_digit = True
        assert found_first_digit, 'no digits in pattern'
        self.re_pattern = re.compile(regex_str)
        self.re_str = regex_str
        self.regex = re.compile(regex_str)
        self.nice_str = disp_str
        assert leading_digit is not None
        assert trailing_digit is not None
        self.leading_digit = leading_digit
        self.trailing_digit = trailing_digit
        self.disp_stdkmd = _regexToStdkmd(regex_str)

        # swap order to go smallest to largest
        pattern_num = pattern_num[::-1]
        pattern_rep = pattern_rep[::-1]
        # track previous digits in number so far (n*prev_b + prev_c)
        prev_b = 0
        prev_c = 0
        # track the numerator polynomial with terms in the form a*(base)^(b*n)
        # implicitly consider the denominator to be (base - 1) (handled later)
        poly = NrrPoly(base)

        # form terms for each component (single digit or repeated)
        assert len(pattern_num) == len(pattern_rep)
        for i in range(len(pattern_num)):
            d = pattern_num[i]
            if pattern_rep[i]:
                # first add repetition of (b+1)*n + c digits
                # d * ( (base)^((prev_b+1)*n + c) - 1 ) / (base - 1)
                # then subtract repetition of b*n + c digits
                # d * ( (base)^(prev_b*n + c) - 1 ) / (base - 1)
                poly_a = NrrPoly(base,-1,*((0,)*prev_b),base**prev_c)
                poly_b = NrrPoly(base,*((0,)*prev_b),base**prev_c) \
                    - NrrPoly(base,1)
                poly += NrrPoly(base,d) * (poly_a - poly_b)
                prev_b += 1
            else:
                # single digit at position b*n+c, d * base^(b*n + c)
                # multiply by the base - 1 denominator
                poly += NrrPoly(base,*((0,)*prev_b),d*base**prev_c*(base-1))
                prev_c += 1

        # divide out common factor from the polynomial
        # then the final polynomial is self.mult * self.poly
        g = math.gcd(*poly.coefs)
        poly //= NrrPoly(base,g)
        self.mult = Fraction(g,(base-1))
        self.poly = poly

        # deduplication by keys is not easy to do rigorously with offsets
        # removing the common coefficient factors is easy but coming up with
        # a bound for checking offsets for a canonical form is not trivial

        # one possible idea that probably works well enough is to store a few
        # keys for a sequence by shifting its index a few times
        # and dividing common factors
        # then pick the lexicographic min coefficient vector

        # the more mathematically correct deduplication is to
        # compare sequence pairs, which makes deduplication time quadratic

    def __call__(self,n:int,/) -> int:
        '''
        evaluate the sequence at an index
        '''
        ret = self.mult.numerator * self.poly(n)
        quot,rem = divmod(ret,self.mult.denominator)
        assert rem == 0
        return quot

    def exprString(self,div='//',exp='**',/) -> str:
        ''' typical expression string format for programming '''
        numer,denom = self.mult.as_integer_ratio()
        polystr = str(self.poly).replace('//',div).replace('**',exp)
        if denom == 1:
            return polystr if numer == 1 else f'{numer}*({polystr})'
        else:
            return f'({polystr}){div}{denom}' if numer == 1 else \
                    f'{numer}*({polystr}){div}{denom}'

    def latexString(self,/) -> str:
        ''' latex code for nice expression display '''
        numer,denom = self.mult.as_integer_ratio()
        latexstr = self.poly.latex()
        if denom == 1:
            return latexstr if numer == 1 else \
                f'{numer}\\times\\left({latexstr}\\right)'
        else:
            return f'{{{latexstr}\\over{denom}}}' if numer == 1 else \
                f'{numer}\\times{{{latexstr}\\over{denom}}}'

    def checkWithEval(self,nmax:int=10,writeResults:bool=False):
        ''' an assert function to make sure the expression generator works '''
        expr = self.exprString()
        for n in range(nmax):
            v = eval(expr,{'n':n})
            assert v == self(n)
            s1 = str(v)
            s2 = ''
            vv = v
            while vv > 0:
                s2 += '0123456789abcdefghijklmnopqrstuvwxyz'[vv%self.base]
                vv //= self.base
            s2 = s2[::-1]
            if writeResults:
                print(f'index {n} (base 10: {s1}) '
                      f'(base {self.base}: {repr(s2)})')
            assert n == 0 or self.regex.fullmatch(s2)

def _nrrSortKeyHelper(base:int,nrr:NrrPattern,/):
    # define a sorting order to try to match stdkmd.net selections
    # this also provides a way of selecting a "best" alternative
    # 1. prioritize those ending in digits coprime to base
    # 2. pick the smallest numerator (prefer no multiply)
    # 3. pick the largest denominator (divide out factors if any)
    # 4. pick by smallest polynomial coefficienst starting from leading

    numer,denom = nrr.mult.as_integer_ratio()
    ret = (numer,-denom,nrr.poly.coefs[::-1])

    # prioritizing those that end in digits coprime to base
    if math.gcd(base,nrr.trailing_digit) == 1:
        ret = (0,*ret)
    else:
        ret = (1,*ret)

    # prioritize by sort tag
    return (nrr.sort_tag,*ret)

def _nrrSortKey(base:int,/):
    # create the sort key for a base
    return lambda nrr : _nrrSortKeyHelper(base,nrr)

def createStandardNrrs(base:int,/,*,
                       aaaaa_gen:bool = True,
                       aaaaa_tag:int = 0,
                       aaaab_gen:bool = True,
                       aaaab_tag:int = 0,
                       abbbb_gen:bool = True,
                       abbbb_tag:int = 0,
                       aaaba_gen:bool = True,
                       aaaba_tag:int = 0,
                       abaaa_gen:bool = True,
                       abaaa_tag:int = 0,
                       abbba_gen:bool = True,
                       abbba_tag:int = 0,
                       abbbc_gen:bool = True,
                       abbbc_tag:int = 0,
                       aabaa_gen:bool = True,
                       aabaa_tag:int = 0,
                       # TODO maybe enable even palindrome
                       aaabbaaa_gen:bool = False,
                       aaabbaaa_tag:int = 0,
                       run_checks:bool = False) \
        -> list[NrrPattern]:
    '''
    create all nrr patterns for a given base matching one of
    - AA..AA (repdigit)
    - AA..AAB (near repdigit)
    - ABB..BB (near repdigit)
    - AA..AABA (near repdigit)
    - ABAA..AA (near repdigit)
    - ABB..BBA (plateau/depression)
    - AA..AABAA..AA (near repdigit palindrome)
    - ABB..BBC (quasi repdigit)
    TODO consider adding even palindrome (AA..AABBAA..AA)
    '''
    assert 2 <= base <= 36
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    d0 = [(i,digits[i]) for i in range(base)]
    d1 = d0[1:]

    nrrs: list[NrrPattern] = []
    for av,ad in d1:
        # AA..AA
        if aaaaa_gen:
            nrrs.append(NrrPattern(base,f'{ad}*',aaaaa_tag))

        for bv,bd in d0:
            if av != bv:
                if bv != 0:
                    # AA..AAB
                    if aaaab_gen:
                        nrrs.append(NrrPattern(base,f'{ad}*{bd}',aaaab_tag))
                    # ABB..BB
                    if abbbb_gen:
                        nrrs.append(NrrPattern(base,f'{ad}{bd}*',abbbb_tag))
                # AA..AABA
                if aaaba_gen:
                    nrrs.append(NrrPattern(base,f'{ad}*{bd}{ad}',aaaba_tag))
                # ABAA..AA
                if abaaa_gen:
                    nrrs.append(NrrPattern(base,f'{ad}{bd}{ad}*',abaaa_tag))
                # ABB..BBA
                if abbba_gen:
                    nrrs.append(NrrPattern(base,f'{ad}{bd}*{ad}',abbba_tag))
                # AA..AABAA..AA
                if aabaa_gen:
                    nrrs.append(NrrPattern(base,f'{ad}*{bd}{ad}*',aabaa_tag))

                # TODO maybe include AA..AABBAA..AA
                if aaabbaaa_gen:
                    nrrs.append(NrrPattern(base,f'{ad}*{bd}{bd}{ad}*',aaabbaaa_tag))

                for cv,cd in d1:
                    if cv != av and cv != bv:
                        # ABB..BBC
                        if abbbc_gen:
                            nrrs.append(NrrPattern(base,f'{ad}{bd}*{cd}',abbbc_tag))

    if run_checks:
        for nrr in nrrs:
            nrr.checkWithEval()

    return nrrs

class NrrCollection:
    '''
    represents a selection of NrrPattern objects
    - manages grouping them by uniqueness up to offset and multiplier
    - using quadratic time algorithm by comparing pairs
    '''

    def __init__(self,base:int,/):
        assert 2 <= base <= 36
        self.base = base
        # each "set" of NrrPattern is a list
        # starting with the representative pattern
        # the representative is determined by the sorting order
        self.nrrsets: list[list[NrrPattern]] = []
        self.compkey = _nrrSortKey(base)

    def add(self,nrr:NrrPattern,/):
        '''
        add nrr into the correct uniqueness set if it does not exist yet
        - this takes linear time, so quadratic to deduplicate all
        - TODO it may be reasonable to store a few extra offsets
          which in practice may be good enough to deduplicate in linear time
          by choosing an offset range [-M,M], maybe M=5 is reasonable
        '''
        assert self.base == nrr.base
        added = False
        for nrrset in self.nrrsets:
            comp1 = nrr.poly.compareShiftAndMultiply(nrrset[0].poly)
            comp2 = nrrset[0].poly.compareShiftAndMultiply(nrr.poly)
            if comp1 is not None:
                assert comp2 is not None
                k1,s1 = comp1
                k2,s2 = comp2
                assert s1 + s2 == 0
                assert k1 * k2 == 1
                if not any(nrr == item for item in nrrset):
                    nrrset.append(nrr)
                    nrrset.sort(key=self.compkey)
                    added = True
                    break
            else:
                assert comp2 is None
        if not added:
            self.nrrsets.append([nrr])

    def fullCheck(self,/):
        '''
        assert function for checking some conditions
        - quadratic time
        '''
        map2index: dict[NrrPattern,int] = dict()
        for i,nrrset in enumerate(self.nrrsets):
            for nrr in nrrset:
                map2index[nrr] = i
        nrrlist = list(map2index)
        for i,nrr1 in enumerate(nrrlist):
            for j in range(i,len(nrrlist)):
                nrr2 = nrrlist[j]
                assert nrr1.base == nrr2.base
                assert i == j or nrr1.re_str != nrr2.re_str
                if map2index[nrr1] == map2index[nrr2]:
                    comp1 = nrr1.poly.compareShiftAndMultiply(nrr2.poly)
                    comp2 = nrr2.poly.compareShiftAndMultiply(nrr1.poly)
                    assert comp1 is not None
                    assert comp2 is not None
                    k1,s1 = comp1
                    k2,s2 = comp2
                    assert s1 + s2 == 0
                    assert k1 * k2 == 1
                    if i == j:
                        assert s1 == 0
                        assert k1 == 1
                    # nrr1(n) = k1 * nrr2(n + s1)
                    n0 = max(0,-s1)
                    k1n,k1d = (k1*nrr1.mult/nrr2.mult).as_integer_ratio()
                    for n in range(n0,n0+10):
                        quot,rem = divmod(k1n*nrr2(n+s1),k1d)
                        assert rem == 0
                        assert nrr1(n) == quot
                    # nrr2(n) = k2 * nrr1(n + s2)
                    n0 = max(0,-s2)
                    k2n,k2d = (k2*nrr2.mult/nrr1.mult).as_integer_ratio()
                    for n in range(n0,n0+10):
                        quot,rem = divmod(k2n*nrr1(n+s2),k2d)
                        assert rem == 0
                        assert nrr2(n) == quot
                else:
                    assert nrr1.poly.compareShiftAndMultiply(nrr2.poly) is None
                    assert nrr2.poly.compareShiftAndMultiply(nrr1.poly) is None

    def findByStr(self,s:str,/) -> None|NrrPattern:
        '''
        search the collection for the matching pattern
        - supports regex format and the nice stdkmd display string
        - returns only 1 if found (there should never be more than 1)
        '''
        for nrrset in self.nrrsets:
            for nrr in nrrset:
                if nrr.re_str == s or _regexToStdkmd(nrr.re_str) == s:
                    return nrr
        return None

    def findByPoly(self,p:NrrPoly,/) -> list[NrrPattern]:
        '''
        search the collection for all patterns with the given polynomial
        - this does not check multipliers
        '''
        assert p.base == self.base
        ret: list[NrrPattern] = []
        for nrrset in self.nrrsets:
            for nrr in nrrset:
                if nrr.poly == p:
                    ret.append(nrr)
        return ret

    def findByFormula(self,m:Fraction,p:NrrPoly,/) -> None|NrrPattern:
        '''
        search the collection for a pattern with the given formula
        - this does not consider others equivalent by shift/multiplier
        - formula must match exactly as provided in the arguments
        '''
        assert p.base == self.base
        for nrrset in self.nrrsets:
            for nrr in nrrset:
                if nrr.mult == m and nrr.poly == p:
                    return nrr
        return None

    def findByEquivalence(self,p:NrrPoly,/) -> None|tuple[NrrPattern,...]:
        '''
        search the collection for the equivalence class
        matching the given polynomial
        '''
        assert p.base == self.base
        for nrrset in self.nrrsets:
            if nrrset[0].poly.compareShiftAndMultiply(p) is not None:
                return tuple(nrrset)
        return None

    def factorByEquivalence(self,nrr:NrrPattern,/) \
            -> tuple[None|tuple[NrrPattern,...],...]:
        '''
        uses this collection to split nrr into factors if possible
        - each factor is represented by the equivalence class
        - the factors may not match a stored pattern exactly
        '''
        assert nrr.base == self.base
        nrr_factors = nrr.poly.factor()
        assert nrr_factors[0] == NrrPoly(self.base,1)
        return tuple(self.findByEquivalence(factor)
                     for factor in nrr_factors[1:])

    def factorByFormula(self,nrr:NrrPattern,/) \
            -> tuple[None|tuple[Fraction,int,NrrPattern],...]:
        '''
        factors by equivalence and then creates a formula in terms of the
        representative element for each equivalence class
        - each found sequence becomes (k,s,f(n)) meaning the component
          of the product is k * f(n+s) (k is a Fraction, s is an int)
        - the components multiply to the polynomial only, nrr.mult must
          also be included to get the correct result
        '''
        assert nrr.base == self.base
        nrr_factors = nrr.poly.factor()
        assert nrr_factors[0] == NrrPoly(self.base,1)
        nrr_factors = nrr_factors[1:]
        nrr_equiv = tuple(self.findByEquivalence(factor)
                          for factor in nrr_factors)
        ret: tuple[None|tuple[Fraction,int,NrrPattern],...] = ()
        for i,nrr_factor in enumerate(nrr_factors):
            nrr_set = nrr_equiv[i]
            if nrr_set is None:
                ret = (*ret,None)
                continue
            comp = nrr_factor.compareShiftAndMultiply(nrr_set[0].poly)
            assert comp is not None
            k,s = comp
            ret = (*ret,(k/nrr_set[0].mult,s,nrr_set[0]))
        if all(nrr_data is not None for nrr_data in ret):
            n0 = max(0,*(-s0 for _,s0,_ in ret)) # type:ignore
            for n in range(n0,n0+10):
                mult = Fraction(1)
                prod = 1
                for k,s,nrr_rep in ret: # type:ignore
                    mult *= k
                    prod *= nrr_rep(n+s)
                mult *= nrr.mult
                quot,rem = divmod(mult.numerator*prod,mult.denominator)
                assert rem == 0
                assert quot == nrr(n)
        return ret

def analyzeStdkmd():
    '''
    perform an analysis of nrr patterns on stdkmd.net
    '''
    raw_nrrs = createStandardNrrs(10,aaabbaaa_gen=False,run_checks=True)
    print(f'created {len(raw_nrrs)} raw nrr patterns')
    assert len(set(nrr.nice_str for nrr in raw_nrrs)) == len(raw_nrrs)
    assert len(set(nrr.disp_stdkmd for nrr in raw_nrrs)) == len(raw_nrrs)
    for nrr in raw_nrrs:
        print(f'    {nrr.nice_str} ({nrr.disp_stdkmd}) -> {nrr.exprString()}')
        nrr.checkWithEval()
    nrrcol = NrrCollection(10)
    for nrr in raw_nrrs:
        nrrcol.add(nrr)
    print(f'found {len(nrrcol.nrrsets)} equivalence classes')
    nrrcol.fullCheck()
    #for nrrset in nrrcol.nrrsets:
    #    print(f'    {' '.join(nrr.disp_stdkmd for nrr in nrrset)}')

    # stdkmd patterns (11111 and 10001 have pages in different format)
    stdkmd_list = [
        '10003', '10004', '10007', '10008', '10009', '10111', '11101', '11113', '11117', '11119',
        '11121', '11131', '11141', '11151', '11161', '11171', '11181', '11191', '11311', '11411',
        '11511', '11611', '11711', '11811', '11911', '12111', '12223', '12227', '12229', '13111',
        '13331', '13333', '13337', '13339', '14111', '14441', '14444', '14447', '14449', '15111',
        '15551', '15553', '15557', '15559', '16111', '16661', '16663', '16667', '16669', '17111',
        '17771', '17773', '17777', '17779', '18111', '18881', '18883', '18888', '18889', '19111',
        '19991', '19993', '19997', '19999',

        '20003', '20009', '21111', '21112', '21113', '21114', '21116', '21117', '21118', '21119',
        '21222', '22122', '22221', '22223', '22227', '22229', '22252', '22272', '22292', '22322',
        '22522', '22722', '22922', '23222', '23332', '23333', '23336', '23339', '24441', '24443',
        '24447', '24449', '25222', '25551', '25552', '25554', '25556', '25557', '25558', '25559',
        '26663', '26669', '27771', '27772', '27773', '27774', '27777', '27779', '28881', '28883',
        '28887', '28889', '29222', '29992', '29993', '29996', '29998', '29999',

        '30001', '30002', '30004', '30007', '30008', '31111', '31113', '31117', '31119', '31333',
        '32221', '32223', '32224', '32226', '32227', '32228', '32229', '32333', '33133', '33313',
        '33323', '33331', '33337', '33343', '33353', '33373', '33383', '33533', '33733', '33833',
        '34333', '34442', '34443', '34444', '34446', '34447', '34448', '34449', '35333', '35551',
        '35553', '35557', '35559', '36661', '36662', '36664', '36667', '36668', '37333', '37771',
        '37773', '37777', '37779', '38333', '38881', '38882', '38883', '38884', '38887', '38888',
        '38889', '39991', '39997',

        '40001', '40003', '40007', '40009', '41111', '41112', '41113', '41114', '41116', '41117',
        '41118', '41119', '41444', '42221', '42223', '42227', '42229', '43331', '43333', '43334',
        '43336', '43337', '43339', '43444', '44344', '44414', '44434', '44441', '44443', '44447',
        '44449', '44474', '44494', '44544', '44944', '45444', '45552', '45553', '45554', '45556',
        '45557', '45558', '45559', '46661', '46663', '46667', '47444', '47771', '47772', '47774',
        '47776', '47777', '47778', '47779', '48881', '48883', '48887', '48889', '49991', '49992',
        '49993', '49994', '49997', '49999',

        '50003', '50006', '50008', '50009', '51111', '51113', '51115', '51117', '51119', '51555',
        '52221', '52222', '52223', '52224', '52225', '52226', '52227', '52228', '52229', '52555',
        '53333', '53335', '53339', '53555', '54441', '54442', '54443', '54444', '54445', '54447',
        '54448', '54449', '54555', '55155', '55255', '55355', '55455', '55515', '55535', '55545',
        '55551', '55552', '55553', '55557', '55559', '55655', '55755', '55855', '55955', '56555',
        '56662', '56663', '56665', '56666', '56668', '56669', '57555', '57771', '57773', '57775',
        '57777', '57779', '58555', '58881', '58882', '58884', '58885', '58886', '58887', '58888',
        '58889', '59555', '59993', '59995', '59999',

        '60001', '60005', '60007', '61111', '61112', '61113', '61114', '61117', '61118', '61119',
        '61666', '62221', '62225', '62227', '62229', '63331', '63332', '63334', '63335', '63337',
        '63338', '64441', '64443', '64445', '64447', '64449', '65551', '65552', '65553', '65554',
        '65556', '65557', '65558', '65559', '65666', '66166', '66616', '66661', '66667', '67666',
        '67772', '67773', '67774', '67775', '67776', '67777', '67778', '67779', '68881', '68883',
        '68885', '68887', '68889', '69991', '69992', '69994', '69995', '69997', '69998',

        '70001', '70003', '70004', '70006', '70009', '71111', '71113', '71115', '71117', '71119',
        '71777', '72221', '72223', '72224', '72226', '72227', '72229', '72777', '73331', '73333',
        '73339', '73777', '74441', '74442', '74443', '74444', '74445', '74446', '74447', '74448',
        '74449', '74777', '75551', '75553', '75557', '75559', '75777', '76661', '76663', '76664',
        '76667', '76669', '76777', '77177', '77277', '77377', '77477', '77577', '77677', '77717',
        '77727', '77737', '77747', '77757', '77767', '77771', '77772', '77773', '77779', '77787',
        '77797', '77877', '77977', '78777', '78882', '78883', '78884', '78885', '78886', '78887',
        '78888', '78889', '79777', '79991', '79993', '79997', '79999',

        '80003', '80005', '80009', '81111', '81112', '81113', '81114', '81115', '81116', '81117',
        '81118', '81119', '81888', '82221', '82223', '82225', '82227', '82229', '83333', '83336',
        '83338', '83339', '83888', '84441', '84443', '84445', '84447', '84449', '85551', '85552',
        '85553', '85556', '85557', '85559', '85888', '86663', '86665', '86669', '87771', '87772',
        '87773', '87774', '87775', '87776', '87777', '87778', '87779', '87888', '88188', '88388',
        '88588', '88788', '88818', '88838', '88858', '88878', '88881', '88883', '88887', '88889',
        '88988', '89888', '89992', '89993', '89995', '89996', '89998', '89999',

        '90001', '90002', '90004', '90005', '90007', '90008', '91111', '91113', '91115', '91117',
        '91119', '91999', '92221', '92222', '92223', '92224', '92225', '92226', '92227', '92228',
        '92229', '92999', '93335', '93337', '94441', '94442', '94443', '94446', '94447', '94448',
        '94449', '94999', '95551', '95553', '95557', '95559', '95999', '96661', '96662', '96664',
        '96665', '96667', '96668', '97771', '97773', '97775', '97777', '97999', '98881', '98882',
        '98883', '98884', '98885', '98886', '98887', '98888', '98889', '98999', '99199', '99299',
        '99499', '99599', '99799', '99899', '99919', '99929', '99949', '99959', '99979', '99989',
        '99991', '99992', '99997',

        '10001', '11111']

    print(f'stdkmd.net has {len(stdkmd_list)} patterns')
    print(f'pattern count by starting digit: {', '.join(
        f'{d} ({len([p for p in stdkmd_list if p[0] == d])})' for d in '123456789')}')

    seq_stdkmd: list[list[str]] = []
    for nrrset in nrrcol.nrrsets:
        seq_stdkmd.append([])
        for p in stdkmd_list:
            if p in (nrr.disp_stdkmd for nrr in nrrset):
                seq_stdkmd[-1].append(p)

    assert max(len(s) for s in seq_stdkmd) == 1, 'something is duplicated on stdkmd.net'

    not_on_stdkmd: list[tuple[str,list[NrrPattern],NrrPattern]] = []
    yes_on_stdkmd: dict[str,tuple[str,bool,list[NrrPattern],NrrPattern]] = dict()
    count_same = 0
    count_all = 0
    seq_class_representatives: list[NrrPattern] = []
    for i,nrrset in enumerate(nrrcol.nrrsets):
        nrr_choice = nrrset[0]
        seq_class_representatives.append(nrr_choice)
        out_str = ' '.join(f'(\033[94m{nrr.disp_stdkmd}\033[0m)' if nrr == nrr_choice
                           else nrr.disp_stdkmd for nrr in nrrset)
        if len(seq_stdkmd[i]) == 0:
            not_on_stdkmd.append((f'not on stdkmd: {out_str}',nrrset,nrr_choice))
        else:
            stdkmd_pattern = seq_stdkmd[i][0]
            nrr_stdkmd = [nrr for nrr in nrrset if stdkmd_pattern == nrr.disp_stdkmd][0]
            selected_same = (stdkmd_pattern == nrr_choice.disp_stdkmd)
            same_note = f'(\033[{['91','92'][selected_same]}m'\
                f'{['diff','same'][selected_same]}\033[0m)'
            if not selected_same:
                out_str += '\033[93m'
                out_str += f' choice({nrr_choice.exprString()})'
                out_str += f' stdkmd({nrr_stdkmd.exprString()})'
                out_str += '\033[0m'
            yes_on_stdkmd[stdkmd_pattern] = (f'{stdkmd_pattern} {same_note}: {out_str}',
                                             selected_same,nrrset,nrr_choice)
            count_all += 1
            if selected_same:
                count_same += 1

    def _printSetInfo(nrr_selected):
        factors = nrrcol.factorByFormula(nrr_selected)
        if len(factors) >= 2:
            out_str = f'    \033[93mfactors to: {nrr_selected.mult}'
            for factor in factors:
                if factor is None:
                    out_str += f' * (none)'
                    continue
                k,s,nrr_rep = factor
                out_str += f' * ( {k} * [{nrr_rep.disp_stdkmd}](n{s:+}) )'
            out_str += f'\033[0m'
            print(out_str)
            out_str = f'    \033[93mexpr factor: {nrr_selected.mult}'
            for factor in nrr_selected.poly.factor():
                out_str += f' * ({factor})'
            out_str += f'\033[0m'
            print(out_str)

    for stdkmd_pattern in sorted(yes_on_stdkmd):
        msg,selected_same,nrr_list,nrr_selected = yes_on_stdkmd[stdkmd_pattern]
        print(msg)
        for i,nrr in enumerate(nrr_list):
            comp = nrr.poly.compareShiftAndMultiply(nrr_list[0].poly)
            assert comp is not None
            k,s = comp
            k = k * nrr.mult / nrr_list[0].mult
            print(f'    {nrr.disp_stdkmd if i > 0
                         else f'\033[94m{nrr.disp_stdkmd}\033[0m'}: '
                  f'{nrr.exprString()} = '
                  + ('f(n)' if i == 0 else f'({k}) * f(n{s:+})'))
        _printSetInfo(nrr_selected)
        print()

    for msg,nrr_list,nrr_selected in not_on_stdkmd:
        print(msg)
        for i,nrr in enumerate(nrr_list):
            comp = nrr.poly.compareShiftAndMultiply(nrr_list[0].poly)
            assert comp is not None
            k,s = comp
            k = k * nrr.mult / nrr_list[0].mult
            print(f'    {nrr.disp_stdkmd if i > 0
                         else f'\033[94m{nrr.disp_stdkmd}\033[0m'}: '
                  f'{nrr.exprString()} = '
                  + ('f(n)' if i == 0 else f'({k}) * f(n{s:+})'))
        _printSetInfo(nrr_selected)
        print()

    print(f'selected same pattern for {count_same}/{count_all}')

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog='nearrepdigit.py',
        description='find, analyze, and deduplicate near repdigit sequences in various bases')
    parser.add_argument('-b','--base',type=int,help='number base system (2-36)')
    parser.add_argument('--stdkmd',action='store_true',help='analyze stdkmd.net patterns')
    args = parser.parse_args()

    if args.stdkmd:
        if args.base is not None and args.base != 10:
            sys.stderr.write(f'stdkmd.net is only base 10, use "--base 10" or do not specify\n')
            exit(1)
        else:
            analyzeStdkmd()
            exit(0)

    else:
        parser.print_usage(sys.stderr)
        exit(1)
