#!/bin/python3

'''
read id,value from stdin and run prp tests
output id followed by either "probable" or "composite"
'''

import sys
from time import time
from tqdm import tqdm

import gmpy2

for line in tqdm(sys.stdin.read().splitlines()):
    i,v = map(int,line.split())
    tqdm.write(f'factor id {i} ({len(str(v))} digits / {v.bit_length()} bits)',sys.stderr)
    t = time()
    p = gmpy2.is_prime(v) # type:ignore
    s = 'probable' if p else 'composite'
    tqdm.write(f'found to be {s} in {time()-t:.3f} sec',sys.stderr)
    print(f'{i} {s}')
