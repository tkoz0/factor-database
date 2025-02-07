#!/bin/python3

'''
go through the id,value list from stdin and prove primality
more memory may be required for PARI/GP
consider the very small possibility that this finds a bpsw pseudoprime
'''

import sys
from tqdm import tqdm

import cypari2
pari = cypari2.Pari()
pari.allocatemem(0,2000000000)

for line in tqdm(sys.stdin.read().splitlines()):
    i,v = map(int,line.split())
    tqdm.write(f'factor id {i} ({len(str(v))} digits)')
    assert pari.isprime(v)
