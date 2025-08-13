#!/bin/python3

'''
use data from factordb.com to add progress to database
'''

import argparse
import os
import sys
from time import sleep
from tqdm import tqdm
scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

import app.database.factordbCom as db

MAX_DELAY = 60

parser = argparse.ArgumentParser()
parser.add_argument('path',type=str)
parser.add_argument('start',type=int)
parser.add_argument('count',type=int)
parser.add_argument('delay',type=float)
args = parser.parse_args()

sys.stderr.write(f'{args}\n')

itqdm = tqdm(range(args.start,args.start+args.count))
for i in itqdm:
    delay = args.delay
    while True:
        try:
            itqdm.write(f'factoring path={args.path} index={i}')
            db.factorCategoryIndexWithFactorDB(args.path,i)
            break
        except Exception as e:
            itqdm.write(f'exception {type(e)} {str(e)}')
            delay = min(delay*2,MAX_DELAY)
            itqdm.write(f'waiting {delay} seconds')
            sleep(delay)
