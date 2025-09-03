#!/bin/python3

'''
perform the prefactoring and generate data used for database insertion
modify as needed for various sequences, below is an example
'''

import json
import sqlite3
import sys

import gmpy2

from factoring import prefactor_runner
from expreval import expreval

import bases
import primes
import sequences

sys.set_int_max_str_digits(0)

# factoring parameters
lim_tdiv = 10**5
lim_prho = 10**5
ecm_b1_curves = ((2000,2000),(10000,1000),(50000,500))
ecm_threads = 0

# ==============================================================================
# example for near repdigit related factoring
# set dry_run = False to actually run the factoring
# ==============================================================================

dry_run = True
DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'
base = int(sys.argv[1])
stdkmd = sys.argv[2]
assert len(stdkmd) == 5 and all(c in DIGITS[:base] for c in stdkmd)
d0,d1,d2,d3,d4 = stdkmd

if len(sys.argv) == 3:
    index_beg = 0
    # for bases 2-6, do 500 for palindromes and 1000 for all others
    # for bases 7-36, do 250 for palindromes and 500 for all others
    index_end = (250 if (d0 == d1 == d3 == d4 and d0 != d2) else 500) \
        * (1 if base > 6 else 2)
elif len(sys.argv) == 4:
    index_beg = 0
    index_end = int(sys.argv[3])
elif len(sys.argv) == 5:
    index_beg = int(sys.argv[3])
    index_end = int(sys.argv[4])
else:
    raise RuntimeError('too many args')
assert 0 <= index_beg <= index_end

# depends on database file (produced by using sqlite3 and nrrfdb.py)
dbcon = sqlite3.connect('nrrall.db')
dbcur = dbcon.cursor()
dbcur.execute("select expr,latex,path from nrr where base = ? and pattern = ?;",
              (base,stdkmd))
try:
    db_expr,db_latex,db_path = dbcur.fetchone()
except:
    raise RuntimeError('cannot find in database')
assert isinstance(db_expr,str)
assert isinstance(db_latex,str)
assert isinstance(db_path,str)
dbcur.close()
dbcon.close()

def expr(n:int,/) -> str:
    # expression to display on factor tables
    return f'\\[{eval(db_latex,{'n':n})}\\]'

def path() -> str:
    return db_path

def value(n:int,/) -> int:
    return eval(db_expr,{'n':n})

# ==============================================================================

for n in range(index_beg,index_end):
    if not dry_run:
        sys.stderr.write(f'\n\033[94mFACTORING INDEX {n}\033[0m\n')

    v = value(n)

    # number details
    output = {
        'index': n,
        'value': v,
        'expr': expr(n),
        'path': path()
    }

    # (partial) factorization
    if not dry_run:
        output['factors'] = None if v < 2 \
            else prefactor_runner(v,
                                  lim_tdiv=lim_tdiv,
                                  lim_prho=lim_prho,
                                  ecm_b1_curves=ecm_b1_curves,
                                  ecm_threads=ecm_threads,
                                  progress_stream=sys.stderr)
        sys.stderr.write(f'\033[32mCOMPLETED INDEX {n}\033[0m\n')

        # check result
        if v >= 2:
            cof = v
            for f,p,_ in output['factors']: # type:ignore
                assert gmpy2.is_prime(f) == p # type:ignore
                assert 1 < f <= cof
                assert cof % f == 0
                cof //= f
            assert cof == 1

    # output
    if dry_run:
        output['bit_size'] = v.bit_length()
        output['digit_length'] = len(str(v))
        print(json.dumps(output,indent=4))
    else:
        print(json.dumps(output,separators=(',',':')))
    sys.stdout.flush()
