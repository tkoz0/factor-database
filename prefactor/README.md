# prefactoring

Tools for selecting numbers to add to the database and finding small factors.
- `prefactor.py` main function for finding small factors
- `dbfactor.py` factor numbers and produce JSON lines output
- `dbinsert.py` insert to database using JSON lines data from `dbfactor.py`
- `bases.py` utility functions for number bases
- `primes.py` utility functions for primes
- `sequences.py` utility functions for number sequences

Before adding numbers to database, find small factors to remove. The goal is to
almost guarantee that all factors below `2**64` are found. The following steps
were chosen.

1. trial division up to `10**5` (all factors up to 5 digits)
2. pollard rho up to `10**6` iterations (high chance to find 12 digit factors)
3. ecm with `B1=2000` for 2000 curves (very high chance to find small factors)
4. ecm with `B1=10000` for 1000 curves (high chance for 20 digit factors)
5. ecm with `B1=50000` for 500 curves (moderate chance for 25 digit factors)

# trial division

Simple program in `trial_div.c` using `libgmp`. It first divides out factors of
2, 3, and 5 followed by numbers $6n\pm1$ which are not divisible by 2 or 3.
This program outputs all of the small prime factors found, but does not output
the remaining cofactor.

# pollard rho

Simple program in `pollard_rho.c` using `libgmp`. It supports a provided
initialization value ($x_0$) and increment ($b$) for the iteration $g(x)=x^2+b$
which is run up to the provided limit of iterations. It only outputs a single
factor if it finds one (other than 1 or the input number). This program uses
the floyd cycle detection method and is optimized by multiplying 100 of the
differences during the iteration before computing a more expensive greatest
common divisor.

# elliptic curve method

GMP-ECM from https://gitlab.inria.fr/zimmerma/ecm is used. This part of the
prefactoring is the longest and parallelized unlike the other 2 parts. There
are 3 steps, one for each parameter choice.

1. `B1=2000` for up to 2000 curves
2. `B1=10000` for up to 1000 curves if (1) fails to find a factor
3. `B1=50000` for up to 500 curves if (2) fails to find a factor

If GMP-ECM is unable to factor a remaining composite cofactor after this then
the remaining unfactored part is available to be factored later.
