#!/bin/python3

'''
get smallest unknown numbers from database
'''

import argparse
import os
import sys
scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

import app.database.numbers as db

parser = argparse.ArgumentParser()
parser.add_argument('type',type=str,help='unknown,composite,probable')
parser.add_argument('limit',type=int,nargs='?')
args = parser.parse_args()

if args.type == 'unknown':
    gen = db.smallestUnknowns(args.limit)
elif args.type == 'composite':
    gen = db.smallestComposites(args.limit)
elif args.type == 'probable':
    gen = db.smallestProbablePrimes(args.limit)
else:
    sys.stderr.write(f'invalid type: {args.type}\n')
    exit(1)

for row in gen:
    print(f'{row.id} {row.value}')
