# scripts

## `use_factordb_com.py`

Use this to get data from factordb.com. Requires specifying a path, index range
(by start and count), and a delay between requests.

## `get_smallest_incomplete.py`

Use this to get the smallest factors from the database with an incomplete
status (unknown, composite without known factors, probable prime).

## `prove_prps.py`

Use this to read factor IDs and value (1 per line, space separated) to run the
primality proving with PARI/GP.

## `set_proven_primes.py`

Use this to read factor IDs from stdin and set these as prime. Makes sure that
they are initially probable primes.

## `run_prp_unknown.py`

Use this to read factor IDs and value (1 per line, space separated) to run PRP
tests. Outputs number ID and either "probable" or "composite" (space separated).

## `set_prp_results.py`

Use this to read factor IDs followed by "probable" or "composite" (space
separated, 1 per line) and set these results in the database.
