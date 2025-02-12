#!/bin/python3

import argparse

from expreval import expreval

parser = argparse.ArgumentParser()
parser.add_argument('beg',type=int)
parser.add_argument('end',type=int)
parser.add_argument('calc',type=str)
args = parser.parse_args()

for n in range(args.beg,args.end):
    print(n,expreval(args.calc,n))
