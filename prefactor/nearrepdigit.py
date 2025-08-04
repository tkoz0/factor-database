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

def _stringForIntegerWithSign(n:int,/) -> str:
    return f'+{n}' if n >= 0 else str(n)

def _stringForLinearPolynomial(b:int,c:int,var:str='n',/) -> str:
    if b == 0:
        return str(c)
    if c == 0:
        return var if b == 1 else f'{b}*n'
    if b == 1:
        return f'n{_stringForIntegerWithSign(c)}'
    return f'{b}*n{_stringForIntegerWithSign(c)}'

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
    assert 0, s
    raise Exception() # make vscode stop complaining about not returning str

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

    def __init__(self,base:int,pattern:str,/):
        assert 2 <= base <= 36
        digits_str = '0123456789abcdefghijklmnopqrstuvwxyz'
        self.base = base

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
        self.regex = re.compile(regex_str)
        self.disp_nice = disp_str
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
        # track numerator terms found in form (a,b,c) meaning a*(base)^(b*n+c)
        # consider it to have a denominator of base - 1 (handled later)
        summed_terms: list[tuple[int,int,int]] = []

        # form terms for each component (single digit or repeated)
        assert len(pattern_num) == len(pattern_rep)
        for i in range(len(pattern_num)):
            d = pattern_num[i]
            if pattern_rep[i]:
                # first add repetition of (b+1)*n + c digits
                # ( (base)^((prev_b+1)*n + c) - 1 ) / (base - 1)
                # then subtract repetition of b*n + c digits
                # ( (base)^(prev_b*n + c) - 1 ) / (base - 1)
                summed_terms.append((d,prev_b+1,prev_c))
                summed_terms.append((-d,prev_b,prev_c))
                prev_b += 1
            else:
                # single digit at position b*n+c, d * base^(b*n + c)
                # multiply by the base - 1 denominator
                summed_terms.append(((base-1)*d,prev_b,prev_c))
                prev_c += 1

        # convert exponents from b*n+c to b*n
        for i,(a,b,c) in enumerate(summed_terms):
            summed_terms[i] = (a*(base**c),b,0)

        # merge terms with matching exponent
        merged_terms_d: dict[int,int] = dict()
        for a,b,c in summed_terms:
            assert c == 0
            if b not in merged_terms_d:
                merged_terms_d[b] = 0
            merged_terms_d[b] += a

        # sort by exponents in descending order (nonzero terms)
        merged_terms_l: list[tuple[int,int]] = \
            sorted(((merged_terms_d[b],b) for b in merged_terms_d
                    if merged_terms_d[b] != 0),
                   key = lambda z : -z[1])

        # chosen to skip the step of converting exponents like 10^(2n)
        # to 10^(2n+1) if coefficient has factor 10 because some of
        # the later steps/ideas are easier with a more "canonical" form
        #
        # simplify by dividing base out of coefficients
        numer_terms: list[tuple[int,int,int]] = []
        for i,(a,b) in enumerate(merged_terms_l):
            assert a != 0
            #c = 0
            #while a % base == 0:
            #    a //= base
            #    c += 1
            #numer_terms.append((a,b,c))
            numer_terms.append((a,b,0))

        # divide out commmon factor in fraction
        # here we use the base - 1 denominator that was ignored so far
        g = math.gcd(base-1,*(a for a,_,_ in numer_terms))
        numer_terms = [(a//g,b,c) for a,b,c in numer_terms]

        # take out common factor from numerator terms
        m = math.gcd(*(a for a,_,_ in numer_terms))
        numer_terms = [(a//m,b,c) for a,b,c in numer_terms]

        # mult.numer * (numerator terms) / mult.denom
        # guaranteed that numerator terms share no common factor
        assert all(c == 0 for _,_,c in numer_terms)
        self.terms = tuple((a,b) for a,b,_ in numer_terms)
        self.mult = Fraction(m,(base-1)//g)

        # deduplication by keys is not easy to do rigorously with offsets
        # removing the common coefficient factors is easy but coming up with
        # a bound for checking offsets for a canonical form is not trivial

        ### (begin) old code for possible ideas

        # deduplication key meant only for standard form terms with base^(k*n)
        #self.key_index_offset = 0
        #self.key_multiplied = 1
        #self.key_terms = tuple(numer_terms)

        # try shifting the sequence and dividing out common factors
        # pick the lexicographically minimum coefficient vector
        # coming up with a way to do this "correctly" in general is hard

        # it is much easier to determine if 2 sequences are
        # identical up to shift and multiply
        # but deduplication like this requires quadratic time

        # adjust offset to find an identifier for "essentially unique"
        #assert all(c == 0 for _,_,c in key_terms)
        #while all(a % (base**b) == 0 for a,b,_ in key_terms):
        #    key_terms = [(a//(base**b),b,c) for a,b,c in key_terms]
        #    self.key_index_offset += 1
        #self.key_terms = tuple(key_terms)

        ### (end) old code

    def _exprStringNumerator(self,div:str,exp:str,/) -> str:
        ret = ''
        for i,(a,b) in enumerate(self.terms):
            t = ''
            if b == 0:
                t += str(abs(a))
            else:
                if abs(a) != 1:
                    t += f'{abs(a)}*'
                t += f'{self.base}{exp}({_stringForLinearPolynomial(b,0)})'
            if i > 0 and a > 0:
                ret += '+'
            elif a < 0:
                ret += '-'
            ret += t
        return ret

    def exprString(self,div='//',exp='**') -> str:
        ''' typical expression string format for programming '''
        ret = self._exprStringNumerator(div,exp)
        numer,denom = self.mult.as_integer_ratio()
        if denom != 1:
            ret = f'({ret}){div}{denom}'
            if numer != 1:
                ret = f'{numer}*{ret}'
        elif numer != 1:
            ret = f'{numer}*({ret})'
        return ret

    def _latexStringNumerator(self,/) -> str:
        ret = ''
        for i,(a,b) in enumerate(self.terms):
            t = ''
            if b == 0:
                t += str(abs(a))
            else:
                if abs(a) != 1:
                    t += f'{abs(a)}\\times'
                t += f'{self.base}^{{{_stringForLinearPolynomial(b,0)}}}'
            if i > 0 and a > 0:
                ret += '+'
            elif a < 0:
                ret += '-'
            ret += t
        return ret

    def latexString(self,/) -> str:
        ''' latex code for nice expression display '''
        ret = self._latexStringNumerator()
        numer,denom = self.mult.as_integer_ratio()
        if denom != 1:
            ret = f'{{{ret}\\over{denom}}}'
            if numer != 1:
                ret = f'{numer}\\times{ret}'
        elif numer != 1:
            ret = f'{numer}\\times\\left({ret}\\right)'
        return ret

    def checkWithEval(self,nmax:int=10,writeResults:bool=False):
        ''' an assert function to make sure the expression generator works '''
        expr = self.exprString()
        for n in range(nmax):
            v = eval(expr,{'n':n})
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

    DEBUG: bool = False
    DEBUG_L: bool = False # for inner loops

    @staticmethod
    def compareShiftAndMultiply(base:int,left:tuple[tuple[int,int],...],
                                right:tuple[tuple[int,int],...],/) \
                                -> None|tuple[Fraction,int]:
        '''
        check if the sequences are identical up to constant multiple and offset
        returns none if they are not, otherwise the shift and multiply

        base = number base system
        left,right = sequence specification as terms (a,b) meaning a*base^(b*n)
        left represents f(n), right represents g(n)
        searches for K,s so f(n) = K * g(n+s), returns (K,s)

        the method here was found with chatgpt assistance
        '''
        debug = NrrPattern.DEBUG
        debug_l = NrrPattern.DEBUG_L # for inner loops
        if debug:
            print(f'called with base={base} left={left} right={right}')

        def _basePow(f:Fraction) -> int|None:
            # numer/denom = base**p (returns p(int) if exists, otherwise none)
            numer,denom = f.as_integer_ratio()
            if debug_l:
                print(f'_basePow with {numer}/{denom}')
            if numer <= 0: # only exists for positives
                return None
            if numer < denom:
                ret = _basePow(1/f)
                return None if ret is None else -ret
            if denom != 1:
                return None
            bp_exp,bp_val = 0,1
            while bp_val <= numer:
                if bp_val == numer:
                    if debug_l:
                        print(f'_basePow returning {p}')
                    return bp_exp
                bp_exp += 1
                bp_val *= base
            return None

        # all coefficients nonzero
        assert len(left) > 0 and len(right) > 0
        assert all(a != 0 for a,_ in left)
        assert all(a != 0 for a,_ in right)
        # base powers must be same
        if tuple(b for _,b in left) != tuple(b for _,b in right):
            if debug:
                print('base powers not the same')
            return None
        assert len(left) == len(right)
        if len(left) == 1:
            # same term, just a multiply with no shift
            K = Fraction(left[0][0],right[0][0])
            if debug:
                print(f'same term, K = {K}')
            return K,0

        # determine the offset from the first 2 terms
        i,j = left[0][1],left[1][1]
        assert i > j
        p = _basePow(Fraction(left[0][0]*right[1][0],left[1][0]*right[0][0]))
        if p is None or p % (i-j) != 0:
            return None
        s = p // (i-j)
        if debug:
            print(f'found offset s = {s}')
        # now check that we get the same s for each i,j pair
        for lefti in range(len(left)):
            ai,i = left[lefti]
            bi = right[lefti][0]
            for rightj in range(lefti+1,len(right)):
                bj,j = right[rightj]
                aj = left[rightj][0]
                assert i > j
                p = _basePow(Fraction(ai*bj,aj*bi))
                if debug_l:
                    print(f'terms ({ai}*base^{i}) and ({bj}*base^{j}) '
                          f'found p = {p}')
                if p is None or p % (i-j) != 0 or p // (i-j) != s:
                    return None
        if debug:
            print('all offset calculations match s')

        # then determine the multiplier
        i = left[0][1]
        if s < 0:
            K = Fraction(left[0][0]*base**(-i*s),right[0][0])
        else:
            K = Fraction(left[0][0],right[0][0]*base**(i*s))
        if debug:
            print(f'found multiplier K = {K}')
        # and be sure each index gets the same result
        for lefti in range(len(left)):
            ai,i = left[lefti]
            bi = right[lefti][0]
            if s < 0:
                K2 = Fraction(ai*base**(-i*s),bi)
            else:
                K2 = Fraction(ai,bi*base**(i*s))
            if debug_l:
                print(f'terms ({ai}*base^{i}) and ({bi}*base^{i}) '
                      f'with multiplier {K2}')
            if K != K2:
                return None
        if debug:
            print(f'all multiplier calculations match K')

        return K,s

def _nrrSortKeyHelper(base:int,nrr:NrrPattern,/):
    # define a sorting order to try to match stdkmd.net selections
    numer,denom = nrr.mult.as_integer_ratio()
    ret = (numer,-denom,nrr.terms)

    # attempt without nmult
    #terms = tuple((a*nrr.nmult,b) for a,b in nrr.terms)
    #return (-nrr.denom,terms)
    #return (terms,-nrr.denom)

    # attempt by finding those with divisibility
    #if sum(a for a,_ in nrr.terms) % (base-1) == 0:
    #    return (1,nrr.nmult,-nrr.denom,nrr.terms)
    #else:
    #    return (0,nrr.nmult,-nrr.denom,nrr.terms)

    # prioritizing those that end in digits coprime to base
    if math.gcd(base,nrr.trailing_digit) == 1:
        ret = (0,) + ret
    else:
        ret = (1,) + ret

    return ret

def _nrrSortKey(base:int,/):
    # create the sort key for a base
    return lambda nrr : _nrrSortKeyHelper(base,nrr)

def createStandardNrrs(base:int,/,*,
                       aaaaa:bool = True,
                       aaaab:bool = True,
                       abbbb:bool = True,
                       aaaba:bool = True,
                       abaaa:bool = True,
                       abbba:bool = True,
                       aabaa:bool = True,
                       abbbc:bool = True,
                       # TODO maybe enable even palindrome
                       aaabbaaa:bool = False,
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

    returns (list[NrrPattern],list[display string with ..],list[5 digit stdkmd format])
    '''
    assert 2 <= base <= 36
    digits = '0123456789abcdefghijklmnopqrstuvwxyz'
    d0 = [(i,digits[i]) for i in range(base)]
    d1 = d0[1:]

    nrrs: list[NrrPattern] = []
    for av,ad in d1:
        # AA..AA
        if aaaaa:
            nrrs.append(NrrPattern(base,f'{ad}*'))

        for bv,bd in d0:
            if av != bv:
                if bv != 0:
                    # AA..AAB
                    if aaaab:
                        nrrs.append(NrrPattern(base,f'{ad}*{bd}'))
                    # ABB..BB
                    if abbbb:
                        nrrs.append(NrrPattern(base,f'{ad}{bd}*'))
                # AA..AABA
                if aaaba:
                    nrrs.append(NrrPattern(base,f'{ad}*{bd}{ad}'))
                # ABAA..AA
                if abaaa:
                    nrrs.append(NrrPattern(base,f'{ad}{bd}{ad}*'))
                # ABB..BBA
                if abbba:
                    nrrs.append(NrrPattern(base,f'{ad}{bd}*{ad}'))
                # AA..AABAA..AA
                if aabaa:
                    nrrs.append(NrrPattern(base,f'{ad}*{bd}{ad}*'))

                # TODO maybe include AA..AABBAA..AA
                if aaabbaaa:
                    nrrs.append(NrrPattern(base,f'{ad}*{bd}{bd}{ad}*'))

                for cv,cd in d1:
                    if cv != av and cv != bv:
                        # ABB..BBC
                        if abbbc:
                            nrrs.append(NrrPattern(base,f'{ad}{bd}*{cd}'))

    if run_checks:
        for nrr in nrrs:
            nrr.checkWithEval()

    return nrrs

def groupNrrsByEquivalence(nrrs:list[NrrPattern],/,*,
                           run_extra_checks:bool=False) \
                            -> list[list[NrrPattern]]:
    '''
    group nrr patterns by equivalence up to multiplier and index offset
    each list returned is an equivalence class

    this class uses a quadratic time algorithm comparing (almost) all pairs
    a general linear time algorithm with identifier keys is hard to create

    choosing to prefer mathematical rigor to "good enough in practice"
    '''
    ret: list[list[NrrPattern]] = []
    for nrr in nrrs:
        added = False
        for seq_class in ret:
            comp = NrrPattern.compareShiftAndMultiply(
                nrr.base,nrr.terms,seq_class[0].terms)
            if comp is not None: # equivalent to this sequence class
                seq_class.append(nrr)
                added = True
        if not added: # did not match a sequence class so put it in a new one
            ret.append([nrr])

    if run_extra_checks:
        for seq_class in ret:
            for i,nrr1 in enumerate(seq_class):
                for j in range(i,len(seq_class)):
                    nrr2 = seq_class[j]
                    comp1 = NrrPattern.compareShiftAndMultiply(
                        nrr1.base,nrr1.terms,nrr2.terms)
                    comp2 = NrrPattern.compareShiftAndMultiply(
                        nrr2.base,nrr2.terms,nrr1.terms)
                    assert comp1 is not None
                    assert comp2 is not None
                    assert comp1[0] * comp2[0] == 1
                    assert comp1[1] == -comp2[1]

    return ret

def findNrrByPattern(nrrs:list[NrrPattern],p:str,/) -> None|NrrPattern:
    ''' find in a list by regex or stdkmd style pattern identifier '''
    for nrr in nrrs:
        if nrr.regex.pattern == p or _regexToStdkmd(nrr.regex.pattern) == p:
            return nrr
    return None

def analyzeStdkmd():
    '''
    perform an analysis of nrr patterns on stdkmd.net
    '''
    nrrs = createStandardNrrs(10,aaabbaaa=False,run_checks=True)
    print(f'created {len(nrrs)} raw nrr patterns')
    for nrr in nrrs:
        print(f'    {nrr.disp_nice} ({nrr.disp_stdkmd}) -> {nrr.exprString()}')
        nrr.checkWithEval(100)
    seq_classes = groupNrrsByEquivalence(nrrs,run_extra_checks=True)
    print(f'found {len(seq_classes)} equivalence classes')
    assert len(set(nrr.disp_nice for nrr in nrrs)) == len(nrrs)
    assert len(set(nrr.disp_stdkmd for nrr in nrrs)) == len(nrrs)
    #for seq_class in seq_classes:
    #    print(f'    {' '.join(nrr.disp_stdkmd for nrr in seq_class)}')

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
    for seq_class in seq_classes:
        seq_stdkmd.append([])
        for p in stdkmd_list:
            if p in (nrr.disp_stdkmd for nrr in seq_class):
                seq_stdkmd[-1].append(p)

    assert max(len(s) for s in seq_stdkmd) == 1, 'something is duplicated on stdkmd.net'

    not_on_stdkmd: list[tuple[str,list[NrrPattern]]] = []
    yes_on_stdkmd: dict[str,tuple[str,bool,list[NrrPattern]]] = dict()
    count_same = 0
    count_all = 0
    for i,seq_class in enumerate(seq_classes):
        nrr_choice = min(seq_classes[i],key=_nrrSortKey(10))
        out_str = ' '.join(f'(\033[94m{nrr.disp_stdkmd}\033[0m)' if nrr == nrr_choice
                           else nrr.disp_stdkmd for nrr in seq_class)
        if len(seq_stdkmd[i]) == 0:
            not_on_stdkmd.append((f'not on stdkmd: {out_str}',seq_class))
        else:
            stdkmd_pattern = seq_stdkmd[i][0]
            nrr_stdkmd = [nrr for nrr in seq_class if stdkmd_pattern == nrr.disp_stdkmd][0]
            selected_same = (stdkmd_pattern == nrr_choice.disp_stdkmd)
            same_note = f'(\033[{['91','92'][selected_same]}m'\
                f'{['diff','same'][selected_same]}\033[0m)'
            if not selected_same:
                out_str += '\033[93m'
                out_str += f' choice({nrr_choice.exprString()})'
                out_str += f' stdkmd({nrr_stdkmd.exprString()})'
                out_str += '\033[0m'
            yes_on_stdkmd[stdkmd_pattern] = (f'{stdkmd_pattern} {same_note}: {out_str}',
                                             selected_same,seq_class)
            count_all += 1
            if selected_same:
                count_same += 1

    for stdkmd_pattern in sorted(yes_on_stdkmd):
        msg,selected_same,nrr_list = yes_on_stdkmd[stdkmd_pattern]
        print(msg)
        for nrr in nrr_list:
            print(f'    {nrr.disp_stdkmd}: {nrr.exprString()}')

    for msg,nrr_list in not_on_stdkmd:
        print(msg)
        for nrr in nrr_list:
            print(f'    {nrr.disp_stdkmd}: {nrr.exprString()}')
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

########
########
########

'''
specify base and pattern for basic output example

import sys
base = int(sys.argv[1])
pattern = sys.argv[2]
nrr = NrrPattern(base,pattern)
expr = str(nrr.exprString())
print(expr)
print(expr.replace('**','^').replace('//','/'))
print(nrr.latexString())
nrr.checkWithEval(10,True)
nrr.checkWithEval(100)
'''

'''
specific pair comparison analysis example

print('analyzing sequence pair comparison')
#nrr1 = _findNrrByPattern('15555')
#nrr2 = _findNrrByPattern('31111')
nrr1 = _findNrrByPattern('18884')
nrr2 = _findNrrByPattern('94442')
assert nrr1 is not None
assert nrr2 is not None
print(nrr1.exprString())
print(nrr2.exprString())
NrrPattern.DEBUG = True
NrrPattern.DEBUG_L = True
c = NrrPattern.compareShiftAndMultiply(base,nrr1.terms,nrr2.terms)
print(f'compare result: {c}')
'''
