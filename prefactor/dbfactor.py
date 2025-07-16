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
ecm_b1_curves = ((2000,2000),(10000,1000),(50000,500),(250000,250))
ecm_threads = 0

# ==============================================================================
# modify the following section as necessary
# keep the same output format (jsonl)
# below is an example for repunits
# set dry_run = False to actually run the factoring
# ==============================================================================
# DO NOT COMMIT CHANGES FOR SPECIFIC NUMBER SEQUENCES (EXAMPLE ONLY)

dry_run = True

index_beg = int(sys.argv[1])
index_end = int(sys.argv[2])
assert 0 <= index_beg <= index_end

base = int(sys.argv[3])
assert 2 <= base <= 36

def expr(n:int,/) -> str:
    # expression to display on factor tables
    assert 2 <= base <= 36 and n >= 0
    return f'\\[2^{{{n}}}-1\\]' if base == 2 \
        else f'\\[{{{base}^{{{n}}}-1\\over{base-1}}}\\]'

def path() -> str:
    # path to the number table
    assert 2 <= base <= 36
    return f'repunit/{base}'

def value(n:int,/) -> int:
    # integer value
    assert 2 <= base <= 36 and n >= 0
    return sequences.repunit(base,n)

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
