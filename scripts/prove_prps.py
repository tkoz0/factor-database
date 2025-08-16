#!/bin/python3

'''
go through the id,value list from stdin and prove primality
more memory may be required for PARI/GP
consider the very small possibility that this finds a bpsw pseudoprime
'''

import sys
from time import time
from tqdm import tqdm

import cypari2
pari = cypari2.Pari()
pari.allocatemem(sizemax=2**32)
pari.default('parisizemax',2**32)
pari.default('threadsizemax',2**28)
pari.setrand(1000003)

for line in tqdm(sys.stdin.read().splitlines()):
    i,v = map(int,line.split())
    tqdm.write(f'factor id {i} ({len(str(v))} digits / {v.bit_length()} bits)',sys.stderr)
    t = time()
    assert pari.isprime(v)
    tqdm.write(f'proven prime in {time()-t:.3f} sec',sys.stderr)
