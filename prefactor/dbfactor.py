#!/bin/python3

'''
perform the prefactoring and generate data used for database insertion
modify as needed for various sequences, below is an example
'''

import argparse
import json
import sys

import cypari2
pari = cypari2.Pari()

from factoring import prefactor_runner
import bases
import primes
import sequences

# factoring parameters
lim_tdiv = 10**5
lim_prho = 10**6
ecm_b1_curves = ((2000,2000),(10000,1000),(50000,500))

parser = argparse.ArgumentParser()
parser.add_argument('-c','--calc',help='term expression for calculation (use {} for index)',type=str,required=True)
parser.add_argument('-e','--expr',help='term expression for database (use {} for index)',type=str,required=True)
parser.add_argument('-s','--start',help='beginning index',type=int,required=True)
parser.add_argument('-f','--finish',help='ending index (1 past end)',type=int,required=True)
parser.add_argument('-p','--path',help='table path',type=str,required=True)
parser.add_argument('-d','--dry-run',help='show what script will do',action='store_true')
parser.add_argument('-v','--verbose',help='extra output on stderr',action='store_true')
parser.add_argument('-l','--length',help='adjust int to str length limit',type=int)
parser.add_argument('-t','--threads',help='number of threads for ecm',type=int,default=0)
args = parser.parse_args()

if args.length:
    sys.set_int_max_str_digits(args.length)

#print(f'args = {args}')

for n in range(args.start,args.finish):
    # eval is unsafe to use so this should only be used properly by admin
    output = {
        'index': n,
        'value': eval(args.calc.replace('{}','n'),{
            'bases': bases,
            'primes': primes,
            'sequences': sequences,
            'n': n
        }),
        'expr': args.expr.replace('{}',str(n))
    }
    assert isinstance(output['value'],int)
    if not args.dry_run:
        output['path'] = args.path
        progress_stream = None
        if output['value'] > 1:
            if args.verbose:
                progress_stream = sys.stderr
                sys.stderr.write(f'\n\033[94mFACTORING INDEX {n}\033[0m\n')
                sys.stderr.write(f'value = {output['value']}\n')
            output['factors'] = prefactor_runner(output['value'],
                                                 lim_tdiv=lim_tdiv,
                                                 lim_prho=lim_prho,
                                                 ecm_b1_curves=ecm_b1_curves,
                                                 ecm_threads=args.threads,
                                                 progress_stream=progress_stream)
            if args.verbose:
                sys.stderr.write(f'\033[32mCOMPLETED INDEX {n}\033[0m\n')
            # check again
            cof = output['value']
            for f,p,_ in output['factors']:
                assert pari.isprime(f) == p
                assert 1 < f <= cof
                assert cof % f == 0
                cof //= f
            assert cof == 1
        else:
            output['factors'] = None
    print(json.dumps(output,separators=(',',':')))
    sys.stdout.flush()
