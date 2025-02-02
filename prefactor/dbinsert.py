#!/bin/python3

'''
use data from the dbfactor.py script to insert into database
'''

import argparse
import json
import os
import sys

import gmpy2

scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

parser = argparse.ArgumentParser()
parser.add_argument('-p','--path',help='provide or override table path',type=str)
parser.add_argument('-d','--dry-run',help='show actions that would be performed',action='store_true')
parser.add_argument('-i','--input',help='show input json lines',action='store_true')
args = parser.parse_args()

if not args.dry_run:
    import app.database as db

for i,line in enumerate(sys.stdin):
    if args.input:
        print(line.strip())
    data = json.loads(line)
    index = data['index']
    assert isinstance(index,int)
    value = data['value']
    assert isinstance(value,int)
    expr = data['expr']
    assert isinstance(expr,str)
    path = data['path']
    assert path is None or isinstance(path,str)
    if args.path:
        path = args.path
    factors = data['factors']
    assert factors is None or isinstance(factors,list)
    if factors is not None:
        factor_list: list[int] = [f for f,_,_ in factors]
        assert all(gmpy2.is_prime(f) for f in factor_list if f < 2**64) # type:ignore
        assert all(value % f == 0 for f in factor_list)
        if not args.dry_run:
            added,nrow = db.addNumber(value,factor_list)
            if added:
                print(f'\033[92mindex {i} added to database, number id {nrow.id}\033[0m')
            else:
                print(f'\033[93mindex {i} already in database, number id {nrow.id}\033[0m')
        else:
            print(f'insert number {value} with factors {factor_list}')
    if path is not None:
        path = tuple(p for p in path.split('/') if p)
        if not args.dry_run:
            try:
                db.createCategoryNumber(path,index,value,expr)
                print(f'\033[32msuccessfully added index {i} to category\033[0m')
            except Exception as e:
                print(f'\033[31mfailed to add to category: {e}\033[0m')
        else:
            print(f'create /{'/'.join(path)} index {i}')
