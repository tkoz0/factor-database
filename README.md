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
- Requests (2.32.3)
- Tqdm (4.67.1)

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

- caching for pages that take a lot of querties, particularly the factor tables
- setup a python virtual environment as part of the repo
  - requires at least python3.12
  - include a requirements.txt
- implement an api
  - some possible routes below
  - choose get/post where appropriate
  - /api/get_number (get, by id or value)
  - /api/get_factor (get, by id or value)
  - /api/submit_factors (post)
  - /api/list_category (get)
- functions for cleaning up other database data
  - remove unreferenced primes/numbers
- make number page link all factors including old ones
- add account button to close all other sessions
- attempt to submit new factors to factordb.com

# later todos

- look at time limits for quart routes to avoid an infinite loop bug
- look at query planner for various queries in database.py
- support compression for submission data
- make factor page show numbers and factors containing it as a factor
- find a better way to update factors with few operations
- function for removing small factors (64 bit) from the database
- setup more proper testing (quart: app.test_request_context)
- setup database triggers if they make sense anywhere
- organize sample databases into a few different options
  - small (possibly with no numbers)
  - large (with similarities to production)
  - add some more complete factorization data from factordb.com

# feature goals

- contribution details
- number reservation system
  - configurable limit per user
- stats page (make stats.py)
- recent page (make recent.py)
- ecm progress
  - estimate smallest factor size
- factoring time estimates
- JSON API

# misc goals

- experimentally measure ECM runtime and probability of finding factors
- optimize ECM parameter selection to find factors efficiently
- experimentally measure runtime for SNFS/GNFS
- find SNFS polynomials and compare estimated SNFS/GNFS runtime
