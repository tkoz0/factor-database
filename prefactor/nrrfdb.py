'''
near repdigit related (nrr) data usage
uses data from nrrgen.py to produce things for fdb (read from stdin)
'''

from fractions import Fraction
import json
import re
import sys

from nrrpoly import NrrPoly

DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'

def toInt(base:int,value:str) -> int:
    assert 2 <= base <= 36
    ret = 0
    dval = 1
    for d in value[::-1]:
        v = DIGITS.find(d)
        assert v != -1 and v < base
        ret += v*dval
        dval *= base
    return ret

def toStr(base:int,value:int) -> str:
    assert 2 <= base <= 36
    ret = ''
    while value:
        value,d = divmod(value,base)
        ret += DIGITS[d]
    return ret[::-1]

class NrrSetInfo:
    def __init__(self,regex:str,stdkmd:str,mult:Fraction,poly:NrrPoly,
                 factors:list[NrrPoly],equiv:list[tuple[Fraction,int,str]],
                 expr:str,latex:str):
        self.regex = regex
        self.stdkmd = stdkmd
        self.poly_mult = mult
        self.poly = poly
        self.poly_factors = factors
        self.poly_factors_equiv = equiv
        self.equiv_nrrs: list[NrrSetInfo] = []
        self.expr = expr
        self.latex = latex
    def addEquiv(self,regex:str,stdkmd:str,mult:Fraction,poly:NrrPoly,
                 factors:list[NrrPoly],equiv:list[tuple[Fraction,int,str]],
                 expr:str,latex:str):
        self.equiv_nrrs.append(NrrSetInfo(regex,stdkmd,mult,poly,factors,equiv,
                                          expr,latex))

def readNrrs(base:int) -> list[NrrSetInfo]:
    assert 2 <= base <= 36
    letters = ' abcdefghijklmnopqrstuvwxyz'
    digit_re = f'[0-{base-1}]' if base <= 10 else f'[0-9a-{letters[base-10]}]'
    ret: list[NrrSetInfo] = []
    for line in sys.stdin:
        obj = json.loads(line)
        assert isinstance(obj,dict)
        assert obj['base'] == base
        if obj['type'] == 'main':
            is_main = True
            regex = obj['main_regex']
            stdkmd = obj['main_stdkmd']
            poly_mult = obj['main_poly_mult']
            poly_coefs = obj['main_poly_coefs']
            poly_factors = obj['main_poly_factors']
            expr = obj['main_expr']
            latex = obj['main_latex']
            poly_factor_equiv = obj['main_poly_factors_equiv']
        elif obj['type'] == 'extra':
            is_main = False
            main_regex = obj['main_regex']
            main_stdkmd = obj['main_stdkmd']
            assert main_regex == ret[-1].regex
            assert main_stdkmd == ret[-1].stdkmd
            regex = obj['extra_regex']
            stdkmd = obj['extra_stdkmd']
            poly_mult = obj['extra_poly_mult']
            poly_coefs = obj['extra_poly_coefs']
            poly_factors = obj['extra_poly_factors']
            expr = obj['extra_expr']
            latex = obj['extra_latex']
            poly_factor_equiv = obj['extra_poly_factors_equiv']
        else:
            assert 0
        assert isinstance(regex,str)
        assert isinstance(stdkmd,str)
        assert re.fullmatch(f'({digit_re}\\*?)+',regex)
        assert re.fullmatch(f'{digit_re}{{5}}',stdkmd)
        assert isinstance(poly_mult,list)
        assert len(poly_mult) == 2
        mult = Fraction(*poly_mult)
        assert isinstance(poly_coefs,list)
        poly = NrrPoly(base,*poly_coefs)
        assert isinstance(poly_factors,list)
        factors = [NrrPoly(base,*factor) for factor in poly_factors]
        assert isinstance(expr,str)
        assert isinstance(latex,str)
        assert isinstance(poly_factor_equiv,list)
        equiv = [(Fraction(*k),s,r) for k,s,r in poly_factor_equiv]
        if is_main:
            ret.append(NrrSetInfo(regex,stdkmd,mult,poly,factors,equiv,
                                  expr,latex))
        else:
            ret[-1].addEquiv(regex,stdkmd,mult,poly,factors,equiv,expr,latex)
    return ret

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='nrrfdb.py',
        description='use data from nrrgen.py to get stuff for fdb.tkoz.me')
    parser.add_argument('-b','--base',type=int,help='number base (2-36)',
                        required=True)
    parser.add_argument('--pattern-list',action='store_true',
                        help='list patterns in stdkmd 5 digit format')
    parser.add_argument('--python-lambdas',action='store_true',
                        help='python dict with lambda expressions')
    parser.add_argument('--python-lambdas-and-latex',action='store_true',
                        help='python dict with lambdas and latex string')
    parser.add_argument('--descriptions',action='store_true',
                        help='output ')
    args = parser.parse_args()
    assert args.base is not None and 2 <= args.base <= 36

    flag_count = 0
    if args.pattern_list:
        flag_count += 1
    if args.python_lambdas:
        flag_count += 1
    if args.python_lambdas_and_latex:
        flag_count += 1
    if args.descriptions:
        flag_count += 1

    if flag_count != 1:
        sys.stderr.write('expected exactly one of:\n'
                         '    --pattern-list\n'
                         '    --python-lambdas\n'
                         '    --python-lambdas-and-latex\n'
                         '    --descriptions\n')
        exit(1)

    nrrdata = sorted(readNrrs(args.base), key = lambda nrrset: nrrset.stdkmd)

    if args.pattern_list:
        for nrrset in nrrdata:
            if len(nrrset.poly_factors) == 1:
                print(nrrset.stdkmd)

    if args.python_lambdas:
        print('nrr_lambdas = {')
        for nrrset in nrrdata:
            if len(nrrset.poly_factors) == 1:
                print(f'    {repr(nrrset.stdkmd)}: lambda n: {nrrset.expr},')
            else:
                pass
                #print(f'  # {repr(nrrset.stdkmd)}: lambda n: {nrrset.expr},')
                #factors_str = ' * '.join(f'({f})' for f in nrrset.poly_factors)
                #print(f'  # factors to: {nrrset.poly_mult} * {factors_str}')
        print('}')

    if args.python_lambdas_and_latex:
        print('nrr_data = {')
        for nrrset in nrrdata:
            latex = nrrset.latex
            latex = latex.replace('{','{{')
            latex = latex.replace('}','}}')
            latex = latex.replace('^{{n}}','^{{{n}}}')
            latex = latex.replace('^{{2n}}','^{{{2*n}}}')
            if len(nrrset.poly_factors) == 1:
                print(f'    {repr(nrrset.stdkmd)}: ((lambda n: {nrrset.expr}), '
                    f"(lambda n: f{repr(latex)})),")
            else:
                pass
                #print(f'  # {repr(nrrset.stdkmd)}: ((lambda n: {nrrset.expr}), '
                #    f"(lambda n: f{repr(latex)})),")
                #factors_str = ' * '.join(f'({f})' for f in nrrset.poly_factors)
                #print(f'  # factors to: {nrrset.poly_mult} * {factors_str}')
        print('}')

    if args.descriptions:
        pass
