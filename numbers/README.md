# guidelines for selecting numbers

Preferred sequences should have the following properties.
This is to limit database size by storing only significant nontrivial results.

- grows at least exponentially
  - something like the fibonacci sequence or repunits are acceptable
  - polynomials grow very slowly so factoring many is trivial
  - storing a large number of smaller easy to factor terms is not the purpose
  - subexponential growth is ok if the number lengths increase quickly
- not trivially factorable
  - some terms may be easy to factor but many should not be, for example
    - repunits of a highly composite power have many smaller factors
    - repunits of other powers usually have larger, hard to find factors
  - fibonacci and repunits have many terms that are hard to factor
  - permutation/combination formulas are trivial to factor
  - sequences of primes are considered trivially factorable
    - primality proving is fast up to a much larger point than factoring
- selected from mathematical significance
  - things with compact representations like fibonacci and repunit
  - related to formulas for important things like combinatorics
  - important random-like sequences like forming integers from pi digits

Another possible criteria is numbers that do not grow too quickly. For example,
fermat numbers grow so fast that only about 15 of them are of suitable size for
this database. However, adding fermat and generalized fermat numbers may still
happen, a clear choice has not been made for the production database yet.

# notes

In `IDEAS.md` is a list of number ideas that may be used to select numbers for
the production database. In `LIST.md` is a list for the production server and a
more specific plan of which numbers to add.
