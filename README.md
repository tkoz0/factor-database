# factor database

Database website for tracking integer factorization progress.

- start factoring from specially selected number sequences (numbers table)
- track intermediate factor results for larger factors (factors table)
- organize numbers into a tree structure of categories and tables
- view and browse information of stored numbers and factorizations
- user accounts (requiring manual creation)
- factor submission (both logged in and anonymously)
- admin interface for editing many parts of the database
- admin scripts for (partial) factoring and primality proving

# dependencies

The following versions were used for development. Other versions should work but
compatibility has not been evaluated yet. Development and production are
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

Clone repository
- `git clone https://github.com/tkoz0/factor-database`

Get Mathjax
- get mathjax and put it at `static/mathjax/tex-svg-full.js`
- available at `https://github.com/mathjax/MathJax/blob/master/es5/tex-svg-full.js`

Sample database
- TODO organize into small and large samples for different purposes
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
- linux service is suggested for production
- see `fdb.service` for a linux service example

# maintenance

TODO needs instructions
- periodically clearing old rows from the logs table
  - TODO make log viewing/clearing an option on an admin page
- adding new numbers to database (TODO do this properly without prefactoring)
- proving primality of probable primes (TODO script for this needs work)
- changing status of unknown numbers (TODO no script for this yet)

# todo

- clean up todo and goal lists
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
- make factors under 2^64 go straight to small primes storage data
  - do not create factor ids for small factors
  - require that submitted factors under 2^64 are prime
- make number page link all factors including old ones
- make factor page link to numbers it divides
  - also other factors it divides
- add a "factored" status on factor pages
- add account button to close all other sessions
- attempt to submit new factors to factordb.com
- icons for category/table instead of the text in parenthesis
  - folder for categories
  - some kind of list/table for tables
- basic info/description on production
  - store in /numbers scripts and jinja templates for certain types
- near repdigit repunit related formulas script
- make this readme better and improve the setup instructions
- use python `/` and `*` for positional/keyword only arguments
- improvements to type annotations
- use column names instead of `*` in sql queries

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
