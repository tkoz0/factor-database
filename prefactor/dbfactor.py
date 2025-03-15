#!/bin/python3

'''
perform the prefactoring and generate data used for database insertion
modify as needed for various sequences, below is an example
'''

import json
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
# modify the following as necessary
# (probably just the cmdline args and the 3 lines below a TODO)
# keep the same output format (jsonl)
# below is an example for repunits
# ==============================================================================

index_beg = int(sys.argv[1])
index_end = int(sys.argv[2])

base = int(sys.argv[3])
assert 2 <= base <= 36

def expr(base:int,n:int,/) -> str:
    # repunit expression
    assert 2 <= base <= 36 and n >= 0
    return f'\\[2^{{{n}}}-1\\]' if base == 2 \
        else f'\\[{{{base}^{{{n}}}-1\\over{base-1}}}\\]'

def path(base:int,/) -> str:
    # repunit table path
    assert 2 <= base <= 36
    return f'repunit/{base}'

for n in range(index_beg,index_end):
    sys.stderr.write(f'\n\033[94mFACTORING INDEX {n}\033[0m\n')
    # TODO adjust computation of number value
    v = sequences.repunit(base,n)
    output = {
        'index': n,
        'value': v,
        # TODO adjust expression to display on factor tables
        'expr': expr(base,n),
        # TODO adjust table path
        'path': path(base),
        'factors': None if v < 2
            else prefactor_runner(v,
                                  lim_tdiv=lim_tdiv,
                                  lim_prho=lim_prho,
                                  ecm_b1_curves=ecm_b1_curves,
                                  ecm_threads=ecm_threads,
                                  progress_stream=sys.stderr)
    }
    sys.stderr.write(f'\033[32mCOMPLETED INDEX {n}\033[0m\n')

    # check result and output
    if v >= 2:
        cof = v
        for f,p,_ in output['factors']:
            assert gmpy2.is_prime(f) == p # type:ignore
            assert 1 < f <= cof
            assert cof % f == 0
            cof //= f
        assert cof == 1
    print(json.dumps(output,separators=(',',':')))
    sys.stdout.flush()
