#!/bin/python3

'''
read id followed by "probable" or "composite" and set results
'''

import os
import sys
from tqdm import tqdm
scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

import app.database.numbers as db

for line in tqdm(sys.stdin.read().splitlines()):
    i,s = line.split()
    i = int(i)
    row = db.getFactorById(i)
    assert row is not None
    if row.primality != db.Primality.UNKNOWN:
        continue
    tqdm.write(f'factor id {i} is {s}',sys.stderr)
    if s == 'probable':
        db.setFactorProbable(i,False)
    elif s == 'composite':
        db.setFactorComposite(i,False)
    else:
        assert 0
