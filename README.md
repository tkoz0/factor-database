# factor database

Database website for tracking integer factorization progress.

- start factoring from specially selected number sequences (numbers table)
- track intermediate factor results for larger factors (factors table)
- organize numbers into a tree structure of categories and tables
- user accounts (requiring manual creation)
- factor submission (both logged in and anonymously)
- admin interface for editing many parts of the database

# dependencies

The following versions were used for development. Other versions should work but
compatibility has not been evaluated yet.

- Python (3.12)
- Quart (0.19)
- PostgreSQL (16)
- Psycopg (3.2.3)
- Gmpy2 (2.2.1)
  - requires libgmp-dev package (ubuntu)
- CyPari2 (2.2.0)
  - requires libpari-dev package (ubuntu)

# installation

For production

- clone repository
- get mathjax files
- setup database
- create config file
- create user(s)
- use hypercorn to run main.py

For development

- clone repository
- setup sample database
- run main.py

# todo

# later todos

- look at time limits for quart routes to avoid an infinite loop bug
- look at query planner for various queries in database.py
- support compression for submission data
- make factor page show numbers and factors containing it as a factor
- make number page link all factors including old ones
- find a better way to update factors with few operations
- function for removing small factors (64 bit) from the database
- functions for cleaning up other database data
- setup more proper testing (quart: app.test_request_context)
- setup a python virtual environment as part of the repo

# feature goals

- contribution details
- number reservation system
  - configurable limit per user
- stats page (make stats.py)
- recent page (make recent.py)
- ecm progress
  - estimate smallest factor size
- factoring time estimates
- database caching
- JSON API

# misc goals

- experimentally measure ECM runtime and probability of finding factors
- optimize ECM parameter selection to find factors efficiently
- experimentally measure runtime for SNFS/GNFS
- find SNFS polynomials and compare estimated SNFS/GNFS runtime
