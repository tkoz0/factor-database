#!/bin/python3

'''
use data from the dbfactor.py script to insert into database
'''

import json
import os
import sys

import gmpy2

scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

import app.database as db

for i,line in enumerate(sys.stdin):
    data = json.loads(line)
    index = data['index']
    assert isinstance(index,int)
    value = data['value']
    assert isinstance(value,int)
    expr = data['expr']
    assert isinstance(expr,str)
    path = data['path']
    assert path is None or isinstance(path,str)
    factors = data['factors']
    assert factors is None or isinstance(factors,list)
    small_factors: list[int] = [f for f,_,_ in factors if f < 2**64]
    assert all(gmpy2.is_prime(f) for f in small_factors) # type:ignore
    added,nrow = db.addNumber(value,small_factors)
    if added:
        print(f'line index {i} added to database, number id {nrow.id}')
    if path is not None:
        path = tuple(p for p in path.split('/') if p)
        db.createCategoryNumber(path,index,value,expr)
