#!/bin/python3

'''
show a summary of the category/table data stored and other database info
'''

import os
import sys
scriptdir = os.path.dirname(__file__)
sys.path.append(f'{scriptdir}/..')

import app.database as db

print(f'Report Timestamp: {db._ts_to_str(db._now())}')
print(f'Database Size: {db.getDatabaseSize()}')
print(f'Numbers Stored: {db.getNumbersCount()}')
print(f'Factors Stored: {db.getFactorsCount()}')
print()

for path,row in db.walkCategories():
    if row.is_table:
        info = db.getCategoryNumberInfo(path,0,1000000)
        indexes = [i for i,_,_,_ in info]
        if indexes == []:
            print(f'/{'/'.join(path)} EMPTY')
        else:
            numlens = [n.value.bit_length() for _,_,n,_ in info if isinstance(n,db.NumberRow)]
            complete_count = sum(1 for _,_,n,_ in info if isinstance(n,db.NumberRow) and n.complete)
            i0,i1 = min(indexes),max(indexes)
            b0,b1 = (0,0) if numlens == [] else (min(numlens),max(numlens))
            print(f'/{'/'.join(path)} '
                f'indexes({i0}-{i1}) '
                f'bitsizes({b0}-{b1}) '
                f'completed({complete_count}/{len(indexes)})')
            if set(indexes) != set(range(i0,i1+1)):
                print(f'    INDEXES CONTAIN GAPS')
