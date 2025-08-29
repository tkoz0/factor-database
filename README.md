# factor database

This is a web app for tracking integer factorization progress.

- start factoring from specially selected number sequences (numbers table)
- track intermediate factor results for larger factors (factors table)
- organize numbers into a tree structure of categories and tables
- view and browse information of stored numbers and factorizations
- user accounts (requiring manual creation)
- factor submission (both logged in and anonymously)
- admin interface for editing many parts of the database
- admin scripts for (partial) factoring and primality proving

# dependencies

The following versions were used for development. Other versions should work
but compatibility has not been evaluated yet. Development and production are
currently using Ubuntu 24.04

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

Setup instructions after cloning the repository assume commands are run at the
repository root unless otherwise stated. File paths are given relative to the
repository root unless otherwise stated.

Recommendations for a production instance
- create a separate linux user for factor database
- use a linux service for production (see fdb.service for an example)
- setup automatic database backups

Clone repository
- `git clone https://github.com/tkoz0/factor-database`

Install the python packages in `requirements.txt`

Get Mathjax
- get mathjax and put it at `static/mathjax/tex-svg-full.js`
- available at `https://github.com/mathjax/MathJax/blob/master/es5/tex-svg-full.js`

Sample database
- for development testing
- run `sample/make_sample_db.py`
- includes administrator account `admin` with password `admin`
- includes regular user account `user` with password `user`

Production setup
- setup a postgres database and user account
- create database tables with `database/schema.sql`
- create `config.json`, see `sample/config.json` for an example
- create user account(s) with python terminal
  - `import app.database as db`
  - `db.createUser('username','email@domain.tld','password','First Last')`
  - `db.setUserAdmin('username',True)`

Running
- for development run `main.py` directly
- for production run `hypercorn main:app`

# maintenance

TODO improve this section

- periodically clearing old rows from the logs table
- adding new numbers to database
  - currently this should be done after prefactoring
  - TODO handle small factors so this is not necessary
- proving primality of probable primes
- changing status of unknown numbers to prime or composite

# todo

- functions for cleaning up other database data
  - remove unreferenced primes/numbers
  - remove old factorizations (without the smallest prime factor)
  - remove factors_old table

- make factors under 2^64 go straight to small primes storage data
  - do not create factor ids for small factors
  - maybe require that submitted factors under 2^64 are prime
  - eliminate the "need" for the prefactoring script

- (pre)factoring
  - support cado-nfs in prefactoring script

- sample database
  - settings for enable/disable components
  - (users, numbers, some factor data, ...)

- pages
  - make number page link all factors including old ones
  - make factor page link to numbers and factors it divides
  - add a "factored" status on factor pages
  - add account button to close all other sessions
  - rework the numbers per page stuff for browsing tables
  - stats page (stats.py)
  - recent page (recent.py)
  - show primes with a green background in the tables

- database
  - attempt to submit new factors to factordb.com
  - consider switching to something like bcrypt for user auth
  - setup a procedure for storing/updating table/category descriptions
    - store text files with descriptions in this repo
  - function to use known factorization to factor another number
    - for example when A and B are already factored and we want to add A\*B

- devops
  - consider creating a docker container

- git repo
  - improve list of sequences

- more numbers
  - script for near repdigit related formulas

- implement api
  - some possible routes below
  - choose get/post where appropriate
  - /api/get_number (get, by id or value)
  - /api/get_factor (get, by id or value)
  - /api/submit_factors (post)
  - /api/list_category (get)

- other todos
  - look at time limits for quart routes to avoid an infinite loop bug
  - look at query planner for various queries in database.py
  - support compression for submission data (and possibly other data)
  - find a better way to update factors with few operations
  - setup more proper testing (quart: app.test_request_context)
  - setup database triggers if they make sense anywhere
  - setup a python virtual environment as part of the repo
    - requires at least python3.12
    - include a requirements.txt
  - caching for expensive pages, particularly the factor tables
  - use column names instead of `*` in sql queries

# feature goals

- contribution details
- number reservation system
  - configurable limit per user
- ecm progress
  - estimate smallest factor size
  - ecm progress can be removed once factored
  - ecm progress is inherited to composite cofactors
- factoring time estimates
- JSON API
- suggested factoring algorithm/parameters (ecm/nfs)
- SNFS polynomials and parameters
- GNFS parameters

# misc goals

- experimentally measure ECM runtime and probability of finding factors
- optimize ECM parameter selection to find factors efficiently
- experimentally measure runtime for SNFS/GNFS
- find SNFS polynomials and compare estimated SNFS/GNFS runtime
