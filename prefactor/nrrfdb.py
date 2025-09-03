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

def toInt(base:int,value:str,/) -> int:
    assert 2 <= base <= 36
    ret = 0
    dval = 1
    for d in value[::-1]:
        v = DIGITS.find(d)
        assert v != -1 and v < base
        ret += v*dval
        dval *= base
    return ret

def toStr(base:int,value:int,/) -> str:
    assert 2 <= base <= 36
    ret = ''
    while value:
        value,d = divmod(value,base)
        ret += DIGITS[d]
    return ret[::-1]

class NrrSetInfo:
    def __init__(self,base:int,regex:str,stdkmd:str,mult:Fraction,poly:NrrPoly,
                 factors:list[NrrPoly],equiv:list[tuple[Fraction,int,str]],
                 expr:str,latex:str):
        self.base = base
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
        self.equiv_nrrs.append(NrrSetInfo(self.base,regex,stdkmd,mult,poly,
                                          factors,equiv,expr,latex))

def readNrrs(base:int,/) -> list[NrrSetInfo]:
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
            ret.append(NrrSetInfo(base,regex,stdkmd,mult,poly,factors,equiv,
                                  expr,latex))
        else:
            ret[-1].addEquiv(regex,stdkmd,mult,poly,factors,equiv,expr,latex)
    return ret

class NrrPageInfo:
    def __init__(self,title:str,info:str,repstr:str):
        self.title = title
        self.info = info
        self.repstr = repstr

def _rep(d:str,/) -> str:
    return f'{d}{d}..{d}{d}'

# where my choices differ from stdkmd
# map my pattern to stdkmd pattern
# this is for generating urls for the stdkmd site
STDKMD_DIFF = {
    '18884': '94442',
    '42225': '84445',
    '14448': '72224',
    '32225': '64445',
    '12228': '61114',
    '12224': '61112',
    '16664': '49992',
    '11112': '10008'
}
# special pages handled differently
STDKMD_SPECIAL = {
    '10001': 'https://stdkmd.net/nrr/repunit/10001.htm',
    '11111': 'https://stdkmd.net/nrr/repunit/'
}

def _few(m:Fraction,nrr:NrrPoly) -> list[int]:
    n,d = m.as_integer_ratio()
    ret: list[int] = []
    for i in range(5):
        v = nrr(i) * n
        v,rem = divmod(v,d)
        assert rem == 0
        ret.append(v)
    return ret

def titleAndRepstr(s:str) -> tuple[str,str]:
    d0,d1,d2,d3,d4 = s
    v0 = DIGITS.find(d0)
    v1 = DIGITS.find(d1)
    v2 = DIGITS.find(d2)
    v3 = DIGITS.find(d3)
    v4 = DIGITS.find(d4)

    if d0 == d1 == d2 == d3 == d4: # AAAAA
        A = d0
        repstr = f'{_rep(A)}'
        title = f'Repunit {repstr}' if v0 == 1 else f'Repdigit {repstr}'
    elif d0 == d1 == d2 == d3 and d3 != d4: # AAAAB
        A,B = d0,d4
        repstr = f'{_rep(A)}{B}'
        title = f'Near Repdigit {repstr}'
    elif d0 != d1 and d1 == d2 == d3 == d4: # ABBBB
        A,B = d0,d1
        repstr = f'{A}{_rep(B)}'
        title = f'Near Repdigit {repstr}'
    elif d0 == d1 == d2 == d4 and d3 != d4: # AAABA
        A,B = d0,d3
        repstr = f'{_rep(A)}{B}{A}'
        title = f'Near Repdigit {repstr}'
    elif d0 == d2 == d3 == d4 and d0 != d1: # ABAAA
        A,B = d0,d1
        repstr = f'{A}{B}{_rep(A)}'
        title = f'Near Repdigit {repstr}'
    elif d0 == d4 and d1 == d2 == d3 and d0 != d1: # ABBBA
        A,B = d0,d1
        repstr = f'{A}{_rep(B)}{A}'
        title = f'Plateau {repstr}' if d0 < d1 \
            else f'Depression {repstr}'
    elif d0 != d1 and d1 == d2 == d3 and d3 != d4 and d0 != d4: # ABBBC
        A,B,C = d0,d2,d4
        repstr = f'{A}{_rep(B)}{C}'
        title = f'Quasi Repdigit {repstr}'
    elif d0 == d1 == d3 == d4 and d1 != d2: # AABAA
        A,B = d0,d2
        repstr = f'{_rep(A)}{B}{_rep(A)}'
        title = f'Near Repdigit Palindrome {repstr}'
    else:
        assert 0, nrrset.stdkmd
    title = f'{nrrset.stdkmd}: {title}'

    return title,repstr

def _seqsym(base:int,regex:str) -> str:
    regex = regex.replace('*','^*')
    regex = ''.join(f'\\text{{{d}}}' if d in DIGITS[10:] else d for d in regex)
    return f'[{regex}_{f'{base}' if base < 10 else f'{{{base}}}'}]'

def makePageInfo(nrrset:NrrSetInfo,/) -> NrrPageInfo:
    base = nrrset.base
    assert re.fullmatch(f'[{DIGITS[:nrrset.base]}]{{5}}',nrrset.stdkmd)
    d0,d1,d2,d3,d4 = nrrset.stdkmd
    v0 = DIGITS.find(d0)
    v1 = DIGITS.find(d1)
    v2 = DIGITS.find(d2)
    v3 = DIGITS.find(d3)
    v4 = DIGITS.find(d4)
    assert 0 < v0 < base
    assert 0 <= v1 < base
    assert 0 <= v2 < base
    assert 0 <= v3 < base
    assert 0 <= v4 < base
    info = ''
    title,repstr = titleAndRepstr(nrrset.stdkmd)

    first_terms = _few(nrrset.poly_mult,nrrset.poly)
    numlist = ','.join(map(str,first_terms)) + ',\\ldots'
    regex_latex = _seqsym(base,nrrset.regex)
    info += f'<p>First few terms (base 10): \\[{regex_latex}_n=\\{{{numlist}\\}}\\]</p>\n'
    if base != 10:
        numlist = ','.join(f'\\text{{{toStr(base,v)}}}' for v in first_terms) + ',\\ldots'
        info += f'<p>First few terms (base {base}): \\[\\{{{numlist}\\}}\\]</p>\n'

    info += f'<p>General Formula:\\[{regex_latex}_n={nrrset.latex}\\]</p>\n'

    if len(nrrset.equiv_nrrs) == 0:
        info += f'<p>Equivalent Patterns: (none)</p>\n'
    else:
        info += f'<p>Equivalent Patterns:'
        for nrr in nrrset.equiv_nrrs:
            # nrrset main is nrrset.poly_mult * nrrset.poly
            # nrr equiv sequence is nrr.poly_mult * nrr.poly
            assert len(nrr.poly_factors_equiv) == 1
            k,s,r = nrr.poly_factors_equiv[0]
            k *= nrr.poly_mult
            n,d = k.as_integer_ratio()
            # k * [r](n+s)
            rleft = _seqsym(base,nrr.regex)
            rright = _seqsym(base,r)
            info += f'\n\\[{rleft}_n=' \
                + (f'{n}\\cdot' if n != 1 else '') \
                + f'{rright}_{f'{{n{s:+}}}' if s != 0 else 'n'}' \
                + (f'/{d}' if d != 1 else '') + f'\\]'
            for i in range(max(0,-s),max(0,-s)+5):
                # v1 = evaluate other sequence
                v1 = nrr.poly(i) * nrr.poly_mult.numerator
                v1,rem = divmod(v1,nrr.poly_mult.denominator)
                assert rem == 0
                # v2 = evaluate main sequence with multiply and shift
                v2 = nrrset.poly_mult.numerator * nrrset.poly(i+s) * n
                v2,rem = divmod(v2,d*nrrset.poly_mult.denominator)
                assert rem == 0
                assert v1 == v2, f'{v1} != {v2}'
        info += '</p>\n'

    if base == 10: # link to relevant stdkmd page
        s = nrrset.stdkmd
        text = f'Factorization of {repstr} on stdkmd.net'
        if s in STDKMD_SPECIAL:
            url = STDKMD_SPECIAL[s]
        else:
            if s in STDKMD_DIFF:
                s = STDKMD_DIFF[s]
                orepstr = titleAndRepstr(s)[1]
                text = f'Factorization of {orepstr} on stdkmd.net'
            url = f'https://stdkmd.net/nrr/{s[0]}/{s}.htm'
        info += f'<p>See Also: <a href="{url}" target="_blank">{text}</a></p>\n'

    return NrrPageInfo(title,info,repstr)

def _nrrfactorstr(nrrset:NrrSetInfo) -> str:
    assert len(nrrset.poly_factors) > 1
    base = nrrset.base
    ret = f'\\[{_seqsym(base,nrrset.regex)}_n={nrrset.latex}='
    if nrrset.poly_mult.numerator != 1:
        ret += f'{nrrset.poly_mult.numerator}\\cdot'
    for factor in nrrset.poly_factors:
        ret += f'\\left({factor.latex()}\\right)'
    if nrrset.poly_mult.denominator != 1:
        ret += f'/{nrrset.poly_mult.denominator}'
    ret += f'='
    if nrrset.poly_mult.numerator != 1:
        ret += f'{nrrset.poly_mult.numerator}\\cdot'
    for k,s,r in nrrset.poly_factors_equiv:
        ret += f'\\left('
        if k.numerator != 1:
            ret += f'{k.numerator}\\cdot'
        ret += f'{_seqsym(base,r)}_{f'{{n{s:+}}}' if s != 0 else 'n'}'
        if k.denominator != 1:
            ret += f'/{k.denominator}'
        ret += f'\\right)'
    if nrrset.poly_mult.denominator != 1:
        ret += f'/{nrrset.poly_mult.denominator}'
    ret += f'\\]'
    return ret

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='nrrfdb.py',
        description='use data from nrrgen.py to get stuff for fdb.tkoz.me')
    parser.add_argument('-b','--base',type=int,help='number base (2-36)',
                        required=True)
    parser.add_argument('--pattern-list',action='store_true',
                        help='list patterns in stdkmd 5 digit format')
    parser.add_argument('--python-prefactor-dict',action='store_true',
                        help='python dict with lambdas, latex strings, etc')
    parser.add_argument('--prefactor-sqlite',action='store_true',
                        help='statements to insert prefactor info for db')
    parser.add_argument('--python-make-categories',action='store_true',
                        help='output code to make the database categories')
    parser.add_argument('--python-set-descriptions',action='store_true',
                        help='output code to set the category descriptions')
    args = parser.parse_args()
    assert args.base is not None and 2 <= args.base <= 36

    flag_count = 0
    if args.pattern_list:
        flag_count += 1
    if args.python_prefactor_dict:
        flag_count += 1
    if args.prefactor_sqlite:
        flag_count += 1
    if args.python_make_categories:
        flag_count += 1
    if args.python_set_descriptions:
        flag_count += 1

    if flag_count != 1:
        sys.stderr.write('expected exactly one of:\n'
                         '  --pattern-list\n'
                         '  --python-prefactor-dict\n'
                         '  --prefactor-sqlite\n'
                         '  --python-make-categories\n'
                         '  --python-set-descriptions\n')
        exit(1)

    nrrdata = sorted(readNrrs(args.base), key = lambda nrrset: nrrset.stdkmd)

    if args.pattern_list:
        for nrrset in nrrdata:
            if len(nrrset.poly_factors) == 1:
                print(nrrset.stdkmd)

    # parsing this hard coded dictionary with a lot of lambdas is impractical
    # for larger bases (combining all 2-36 takes 30sec to load and 4GB of RAM)
    # instead read the nrr data file to get the lambdas for a single pattern
    if args.python_prefactor_dict:
        print(f'nrr_data_base_{args.base} = {{')
        for nrrset in nrrdata:
            s = nrrset.stdkmd
            path = f'nrr/{args.base}/{s[0]}/{s}' if args.base > 6 else f'nrr/{args.base}/{s}'
            latex = nrrset.latex
            latex = latex.replace('{','{{')
            latex = latex.replace('}','}}')
            latex = latex.replace('^{{n}}','^{{{n}}}')
            latex = latex.replace('^{{2n}}','^{{{2*n}}}')
            if len(nrrset.poly_factors) == 1:
                print(f'    {repr(nrrset.stdkmd)}: ({repr(path)}, '
                      f'(lambda n: {nrrset.expr}), '
                      f'(lambda n: f{repr(latex)})),')
            else:
                pass
                print(f'  # {repr(nrrset.stdkmd)}: ({repr(path)}, '
                      f'(lambda n: {nrrset.expr}), '
                      f'(lambda n: f{repr(latex)})),')
                factors_str = ' * '.join(f'({f})' for f in nrrset.poly_factors)
                print(f'  # factors to: {nrrset.poly_mult} * {factors_str}')
        print(f'}}')

    if args.prefactor_sqlite:
        print("create table if not exists nrr (")
        print("    base integer,")
        print("    pattern text,")
        print("    expr text,")
        print("    latex text,")
        print("    path text,")
        print("    primary key (base,pattern)")
        print(") strict;")
        print()
        print("insert into nrr (base,pattern,expr,latex,path) values")
        value_tuples: list[str] = []
        for nrrset in nrrdata:
            if len(nrrset.poly_factors) > 1:
                continue
            expr = nrrset.expr # already formatted as python expression
            latex = nrrset.latex # need to reformat as f string
            latex = latex.replace('{','{{')
            latex = latex.replace('}','}}')
            latex = latex.replace('^{{n}}','^{{{n}}}')
            latex = latex.replace('^{{2n}}','^{{{2*n}}}')
            latex = latex.replace('\\','\\\\')
            path = f'nrr/{args.base}/{nrrset.stdkmd[0]}/{nrrset.stdkmd}' if args.base > 6 \
                else f'nrr/{args.base}/{nrrset.stdkmd}'
            # making sql like this is bad but this is not arbitrary user input
            value_tuples.append(f"({args.base},'{nrrset.stdkmd}','{expr}','f''{latex}''','{path}')")
        for i,value_tuple in enumerate(value_tuples):
            print("    " + value_tuple + ',;'[i == len(value_tuples)-1])
        print()
        print("vacuum;")
    # # the following command can be used to create the database file
    # for b in $(seq 2 36); do cat nrrdata_$b.jsonl
    # | python3 nrrfdb.py -b $b --prefactor-sqlite
    # | sqlite3 nrrall.db; done
    #
    # # then a list of commands to run for prefactoring can be made from
    # for b in $(seq 2 36)
    #     do
    #     for p in $(python3 nrrfdb.py -b $b --pattern-list < nrrdata/nrrdata_$b.jsonl)
    #         do echo ./dbfactor_nrr.py $b $p \> out_nrr_${b}_${p}.jsonl.tmp  \
    #             \&\& mv out_nrr_2_${p}.jsonl{.tmp,} >> NRR_ALL.sh
    #     done \
    #     && echo >> NRR_ALL.sh
    # done

    # for bases 2-6, put all patterns in the same list
    # for bases 7-36, split up by starting digit

    if args.python_make_categories:
        print('import app.database.categories as dbcat')
        print()
        digit_paths: dict[str,str] = dict()
        for i in range(1,args.base):
            d = DIGITS[i]
            digit_paths[d] = f'nrr/{args.base}' \
                + (f'/{d}' if args.base > 6 else '')
            if args.base > 6:
                print(f"dbcat.createCategory('{digit_paths[d]}', is_table = False, "
                      f"title = 'First Digit {d}', info = '')")
        prev_digit = '0'
        all_patterns: set[str] = set()
        for nrrset in nrrdata:
            if len(nrrset.poly_factors) > 1:
                continue
            s = nrrset.stdkmd
            all_patterns.add(s)
            if s[0] != prev_digit:
                print()
                prev_digit = s[0]
            t = nrrset.regex
            for d in DIGITS[:nrrset.base]:
                t = t.replace(f'{d}*',_rep(d))
            print(f"dbcat.createCategory('{digit_paths[s[0]]}/{s}', "
                  f"is_table = True, title = 'Pattern {s}: {t}', info = '')")
            #for nrr in nrrset.equiv_nrrs:
            #    s = nrr.stdkmd
            #    print(f"dbcat.createCategory('nrr/{s[0]}/{s}', "
            #          f"is_table = True, title = 'duplicate', info = '')")
        print()
        if args.base > 6:
            for i in range(1,args.base):
                d = DIGITS[i]
                print(f"dbcat.reorderSubcategories({repr(digit_paths[d])},\n"
                      f"    {repr(list(sorted(s for s in all_patterns if s[0] == d)))})")
        else:
            print(f"dbcat.reorderSubcategories('nrr/{args.base}',\n"
                  f"    {repr(list(sorted(all_patterns)))})")

    if args.python_set_descriptions:
        print('import app.database.categories as dbcat')
        digit_paths: dict[str,str] = dict()
        for i in range(1,args.base):
            d = DIGITS[i]
            digit_paths[d] = f'nrr/{args.base}' \
                + (f'/{d}' if args.base > 6 else '')
        prev_digit = '0'
        per_digit_factors = {DIGITS[i]:[] for i in range(1,args.base)}
        for nrrset in nrrdata:
            s = nrrset.stdkmd
            if s[0] != prev_digit:
                print()
                prev_digit = s[0]
            if len(nrrset.poly_factors) > 1: # factorable
                per_digit_factors[s[0]].append(_nrrfactorstr(nrrset))
                for nrr in nrrset.equiv_nrrs:
                    per_digit_factors[nrr.stdkmd[0]].append(_nrrfactorstr(nrr))
            else: # not factorable
                detail = makePageInfo(nrrset)
                print(f"dbcat.setCategoryTitle('{digit_paths[s[0]]}/{s}',"
                    f"{repr(detail.title)})")
                lines = detail.info.splitlines()
                print(f"dbcat.setCategoryInfo('{digit_paths[s[0]]}/{s}',")
                for i in range(len(lines)):
                    print(f"    {repr(lines[i]+'\n')}"
                        + (')' if i == len(lines)-1 else ''))
        print()
        if args.base > 6:
            for i in range(1,args.base):
                d = DIGITS[i]
                print(f"dbcat.setCategoryTitle('nrr/{args.base}/{d}',"
                      f"'Patterns Starting With {d}')")
                if len(per_digit_factors[d]) == 0:
                    print(f"dbcat.setCategoryInfo('nrr/{args.base}/{d}',\n"
                          f"    '<p>Patterns that can be factored: (none)</p>\\n')")
                else:
                    print(f"dbcat.setCategoryInfo('nrr/{args.base}/{d}',\n"
                          f"    '<p>Patterns that can be factored:\\n'")
                    last_i = len(per_digit_factors[d])-1
                    for i,data in enumerate(per_digit_factors[d]):
                        print(f"    {repr(data + ('</p>' if i == last_i else '') + '\n')}"
                              + (')' if i == last_i else ''))
        else:
            print(f"dbcat.setCategoryInfo('nrr/{args.base}',\n"
                  f"    '<p>Patterns that can be factored:\\n'")
            per_digit_factors_list = []
            for d in per_digit_factors:
                per_digit_factors_list += per_digit_factors[d]
            last_i = len(per_digit_factors_list)-1
            for i,data in enumerate(per_digit_factors_list):
                print(f"    {repr(data + ('</p>' if i == last_i else '') + '\n')}"
                      + (')' if i == last_i else ''))
