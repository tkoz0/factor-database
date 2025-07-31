'''
helper utilities for database functionality
'''

from datetime import datetime, UTC
import re
import struct
import time
from typing import Iterable

from app.database.constants import \
    TIME_FORMAT, \
    Primality

from app.config import \
    DEBUG_EXTRA, \
    PRP_BIT_LIM, \
    PROVE_BIT_LIM

from app.utils.primeTest import prpTest, primeTest

class FdbException(Exception):
    ''' exception type for database issues '''

def currentTimeUtc() -> datetime:
    ''' current utc time '''
    # note: sqlite3 does not have date type
    # (convert to .timestamp() which is unix float if supporting sqlite3)
    return datetime.now(UTC).replace(tzinfo=None)

def timestampToString(d:datetime,/) -> str:
    ''' convert timestamp to string format used by sqlite3 '''
    return time.strftime(TIME_FORMAT,d.timetuple())

def stringToTimestamp(s:str,/) -> datetime:
    ''' convert string (YYYY-mm-dd HH:MM:SS) to datetime object '''
    st = time.strptime(s,TIME_FORMAT)
    return datetime.fromtimestamp(time.mktime(st)).replace(tzinfo=UTC)

def sqlite3regexp(expr:str,item:str,/) -> bool:
    ''' leftover function attempting to support sqlite3 regexp extension '''
    return re.search(expr,item) is not None

def intToFdbNumber(n:int,/) -> bytes:
    ''' convert nonnegative integer for database storage (to byte array) '''
    return n.to_bytes((n.bit_length()+7)//8,'big',signed=False)

def fdbNumberToInt(b:bytes,/) -> int:
    ''' convert database storage to integer (from byte array) '''
    return int.from_bytes(b,'big',signed=False)

'''
currently small prime factors are stored in 3 byte arrays
each stores 2/4/8 byte prime factors in a raw byte sequence (big endian)
these numbers stored must be prime and sorted in nondecreasing order
spf2 = sequence of primes (p < 2^16)
spf4 = sequence of primes (2^16 < p < 2^32)
spf8 = sequence of primes (2^32 < p < 2^64)
'''

def spfsToFdbFormat(ns:Iterable[int],/) \
                    -> tuple[bytes|None,bytes|None,bytes|None]:
    '''
    convert small prime factors to byte arrays (big endian) for database
    all numbers must be prime, this function sorts them
    returns 3 byte arrays for 16/32/64 bit primes respectively
    '''
    ns = sorted(ns)
    n2 = [n for n in ns if n < 2**16]
    n4 = [n for n in ns if 2**16 <= n < 2**32]
    n8 = [n for n in ns if 2**32 <= n < 2**64]
    if DEBUG_EXTRA:
        assert len(n2) + len(n4) + len(n8) == len(ns)
        assert all(2 <= n <= 65521 for n in n2)
        assert all(65537 <= n <= 2**32 - 5 for n in n4)
        assert all(2**32 + 15 <= n <= 2**64 - 59 for n in n8)
        assert n2 == sorted(n2)
        assert n4 == sorted(n4)
        assert n8 == sorted(n8)
        assert all(primeTest(n) for n in ns)
    return struct.pack(f'>{len(n2)}H',*n2) if len(n2) else None, \
           struct.pack(f'>{len(n4)}I',*n4) if len(n4) else None, \
           struct.pack(f'>{len(n8)}Q',*n8) if len(n8) else None

def fdbFormatToSpfs(b2:bytes|None,b4:bytes|None,b8:bytes|None,/) \
        -> tuple[tuple[int,...],tuple[int,...],tuple[int,...]]:
    '''
    extract small prime factors from database storage
    they will be prime and sorted
    '''
    b2tuple = () if b2 is None else struct.unpack(f'>{len(b2)//2}H',b2)
    b4tuple = () if b4 is None else struct.unpack(f'>{len(b4)//4}I',b4)
    b8tuple = () if b8 is None else struct.unpack(f'>{len(b8)//8}Q',b8)
    if DEBUG_EXTRA:
        assert b2tuple == tuple(sorted(b2tuple))
        assert b4tuple == tuple(sorted(b4tuple))
        assert b8tuple == tuple(sorted(b8tuple))
        assert all(2 <= n <= 65521 for n in b2tuple)
        assert all(65537 <= n <= 2**32 - 5 for n in b4tuple)
        assert all(2**32 + 15 <= n <= 2**64 - 59 for n in b8tuple)
        assert all(primeTest(n) for n in b2tuple+b4tuple+b8tuple)
    return (b2tuple,b4tuple,b8tuple)

def fdbPrimality(n:int,/) -> int:
    '''
    internal basic primality tester, should be fast
    recommended to find small prime divisors and insert them with number first
    further primality results should be computed elsewhere, use scripts to add
    '''
    if n.bit_length() > PRP_BIT_LIM:
        return Primality.UNKNOWN
    if n.bit_length() <= PROVE_BIT_LIM:
        return Primality.PRIME if primeTest(n) else Primality.COMPOSITE
    return Primality.PROBABLE if prpTest(n) else Primality.COMPOSITE

def stringToPath(s:str,/) -> tuple[str,...]:
    ''' convert string to tuple of path components '''
    return tuple(p for p in s.strip(' \n\t/').split('/') if p)

def pathToString(p:tuple[str,...],/):
    ''' convert path components to string (starting with /) '''
    return f'/{'/'.join(p)}'
