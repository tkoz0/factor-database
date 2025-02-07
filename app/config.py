import json
import math
import os
import sys

scriptdir = os.path.dirname(__file__)

# config file has to be first created
with open(f'{scriptdir}/../config.json','r') as f:
    config = json.load(f)
assert isinstance(config,dict)

'''
suggested default
config = {
    'debug_extra': True,
    'num_bit_lim': 65536,
    'pwd_hash_iters': 1024,
    'session_len_days': 90,
    'min_pwd_len': 10,
    'prp_bit_lim': 2048,
    'prove_bit_lim': 256,
    'table_per_page_default': 50,
    'table_per_page_limit': 200,
    'max_content_length': 2**20,
    'max_factors_length': 2**18,
    'max_details_length': 2**19,
    'db_type': 'postgres',
    'db_host': 'localhost',
    'db_port': 5433,
    'db_user': 'test_fdb',
    'db_pass': 'test_fdb',
    'db_name': 'test_fdb',
    'db_con_lim': 64,
    'log_to_file': True,
    'admin_email': 'admin@example.com',
    'proxy_fix_mode': 'none',
    'proxy_fix_hops': 0,
    'pari_mem': 32000000
}
'''

# enable extra debugging stuff for development
#DEBUG_BASIC: bool = config['debug_basic']
DEBUG_EXTRA: bool = config['debug_extra']
#assert isinstance(DEBUG_BASIC,bool)
assert isinstance(DEBUG_EXTRA,bool)
#assert not DEBUG_EXTRA or DEBUG_BASIC

# length limit (in bits) for numbers added to database
# this limit adjusts the python str<->int conversion limit
# use 0 for no limit (not recommended)
NUM_BIT_LIM: int = config['num_bit_lim']
assert isinstance(NUM_BIT_LIM,int)
assert NUM_BIT_LIM > 0

# number of pbkdf2 iterations to use for passwords
PWD_HASH_ITERS: int = config['pwd_hash_iters']
assert isinstance(PWD_HASH_ITERS,int)
assert PWD_HASH_ITERS > 0

# amount of time sessions are valid after logging in
SESSION_LEN_DAYS: int = config['session_len_days']
assert isinstance(SESSION_LEN_DAYS,int)
assert SESSION_LEN_DAYS > 0

# whether or not to renew session expiration time
RENEW_SESSIONS: bool = config['renew_sessions']
assert isinstance(RENEW_SESSIONS,bool)

# minimum password length
MIN_PWD_LEN: int = config['min_pwd_len']
assert isinstance(MIN_PWD_LEN,int)
assert 1 <= MIN_PWD_LEN <= 128

# maximum number of bits allowed for doing PRP tests automatically
PRP_BIT_LIM: int = config['prp_bit_lim']
assert isinstance(PRP_BIT_LIM,int)
assert PRP_BIT_LIM >= 64

# maximum number of bits allowed for doing provable primality tests
PROVE_BIT_LIM: int = config['prove_bit_lim']
assert isinstance(PROVE_BIT_LIM,int)
assert PROVE_BIT_LIM >= 64
assert PROVE_BIT_LIM <= PRP_BIT_LIM

# size of index range to display on number tables
TABLE_PER_PAGE_DEFAULT: int = config['table_per_page_default']
TABLE_PER_PAGE_LIMIT: int = config['table_per_page_limit']
assert 0 < TABLE_PER_PAGE_DEFAULT <= TABLE_PER_PAGE_LIMIT <= 10000

# maximum length for post requests to the web server
# minimum value allowed is 2**16
MAX_CONTENT_LENGTH: int = config['max_content_length']
assert isinstance(MAX_CONTENT_LENGTH,int)
assert MAX_CONTENT_LENGTH >= 2**16

# maximum length for text box to submit factors
MAX_FACTORS_LEN: int = config['max_factors_length']
assert isinstance(MAX_FACTORS_LEN,int)
assert MAX_FACTORS_LEN > 0

# maximum length for text box to submit factorization details
MAX_DETAILS_LEN: int = config['max_details_length']
assert isinstance(MAX_DETAILS_LEN,int)
assert MAX_DETAILS_LEN > 0

# python has an adjustable limit for conversion of int->str or str->int
# default is 4300 and it may be desirable to store longer numbers in database
_ln2_d_ln10 = math.log(2) / math.log(10)
_ndlen = 1 + int(NUM_BIT_LIM * _ln2_d_ln10)
if sys.get_int_max_str_digits() < _ndlen:
    sys.set_int_max_str_digits(_ndlen)

# database details
DB_TYPE: str = config['db_type']
DB_HOST: str = config['db_host']
DB_PORT: int = config['db_port']
DB_USER: str = config['db_user']
DB_PASS: str = config['db_pass']
DB_NAME: str = config['db_name']
# currently only supporting postgres
assert DB_TYPE in ('postgres',) # ('postgres','mysql','sqlite')
assert isinstance(DB_HOST,str)
assert isinstance(DB_PORT,int)
assert isinstance(DB_USER,str)
assert isinstance(DB_PASS,str)
assert isinstance(DB_NAME,str)

# limit on number of connections
DB_CON_LIM: int = config['db_con_lim']
assert isinstance(DB_CON_LIM,int)

# whether to save log details to a file as well
LOG_TO_FILE: bool = config['log_to_file']
assert isinstance(LOG_TO_FILE,bool)

# email address for admin stuff
# may eventually replace with a proper system for password resets
ADMIN_EMAIL: str = config['admin_email']
assert isinstance(ADMIN_EMAIL,str)

# proxy fix middleware settings for hypercorn server
PROXY_FIX_MODE: str|None = config['proxy_fix_mode']
PROXY_FIX_HOPS: int = config['proxy_fix_hops']
assert PROXY_FIX_MODE is None or isinstance(PROXY_FIX_MODE,str)
assert PROXY_FIX_MODE is None or PROXY_FIX_MODE in ('legacy','modern')
assert isinstance(PROXY_FIX_HOPS,int)
assert PROXY_FIX_MODE is None or PROXY_FIX_HOPS > 0

# memory size for pari used to prove primality
PARI_MEM: int = config['pari_mem']
assert isinstance(PARI_MEM,int)
assert PARI_MEM >= 8000000
