#!/bin/python3

'''
use data from factordb.com to add progress to database
'''

import argparse
import os
import sys
scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

import app.database as db

parser = argparse.ArgumentParser()
parser.add_argument('path',type=str)
parser.add_argument('start',type=int)
parser.add_argument('count',type=int)
parser.add_argument('delay',type=float)
args = parser.parse_args()

sys.stderr.write(f'{args}')

db.factorCategoryWithFactorDB(args.path,args.start,args.count,args.delay)
