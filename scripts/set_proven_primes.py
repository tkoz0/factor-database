#!/bin/python3

'''
set probable primes to proven by ids (does not run primality test)
'''

import os
import sys
from tqdm import tqdm
scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

import app.database as db

for line in tqdm(sys.stdin.read().splitlines()):
    # first integer on the line
    i = int(line.split()[0])
    row = db.getFactorByID(i)
    assert row is not None
    if row.primality == db.Primality.PRIME:
        continue
    assert row.primality == db.Primality.PROBABLE
    tqdm.write(f'factor id {i}',sys.stderr)
    db.setFactorPrime(i,False)
