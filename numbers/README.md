# selected numbers for production database

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
- does not grow too fast
  - fermat numbers grow so fast that only a few terms are acceptable size
  - sequences that would have very few terms can be stored elsewhere
  - very big numbers can utilize compact representations
  - this database is designed for storing full representations of numbers

# some ideas

- mersenne
- fermat - grows too quickly
- fibonacci, lucas
- padovan, narayana, perrin
- generalizations of fibonacci and similar sequences
- integer powers plus/minus constant
- factorials plus/minus constant
- primorials plus/minus constant
- double/triple/.. factorials plus/minus constant
- compositorials plus/minus constant
- factorial base repdigit
  - 1! + 2! + ... + n!
- integer parts of pi/e/sqrt(2)/.. times base^power
  - pi: 3, 31, 314, 3141, 31415, 314159, ...
  - e: 2, 27, 271, 2718, 27182, 271828, ...
  - see y-cruncher ideas for more
  - consider both floor and ceiling
- numerator/denominator of convergents to irrationals
- dynamic programming recurrence sequences
- combinatorics formulas
- pell sequences
- n^n plus/minus constant
- 1^1 + 2^2 + 3^3 + ... + n^n
- x^n plus/minus y^n
- repunit with negative base (b^n-1)/(b-1)
- generalized mersenne numbers (a^n-b^n)/(a-b) with gcd(a,b)=1
- wagstaff numbers (2^p+1)/3 (p odd prime)
- generalized wagstaff (b^n+1)/(b+1) (possibly with negative b)
- proth numbers (k\*2^n+1)
- solinas numbers (f(2^k), f is low degree poly with small integer coeffs)
- number of derangements
- number of integer partitions
- odd integer partitions (each partition is odd)
- even integer partitions (might be interesting but can all be divided by 2)
- distinct integer partitions (each partition size is unique)
- bell numbers (set partitions)
- catalan numbers (are these trivially factorable)
- motzkin numbers (ways of drawing lines between points on circle)
- telephone/involution numbers (ways to make graph matchings)
- schroder numbers (count 2d lattice paths with diagonals allowed)
- schroder-hipparchus number (counting plane trees)
- tribonacci numbers
- tetranacci numbers
- other (P,Q) fibonacci/lucas sequences
- determinants of significant matrices
- stirling numbers (are these trivial to factor)
- lah numbers (related to stirling)
- fuss-catalan number
- pseudoprimes (if any types grow fast enough)
- lychrel number sequences
- sums of fibonacci/lucas/other numbers f(0)+f(1)+f(2)+...+f(n)
- fibonacci base ideas (zeckendorf representation)
- extensions of sequences to negative indexes if they give interesting results
- constants for the random fibonacci sequence
- pseudoprimes if there are any types that grow quickly enough
- fibonacci/lucas plus/minus small constant (and other important sequences)

# ideas from oeis.org

- A000055 number of trees with n unlabeled nodes
- A000088 number of simple graphs on n unlabeled nodes
- A000664 number of graphs with n edges
- A001187 number of connected labeled graphs with n nodes
- A001349 number of simple connected graphs on n unlabeled nodes
- A002494 number of n node graphs without isolated nodes

# ideas from stdkmd.net

- repeated digit expressed as AA..AA
- repunit (including bases other than 10)
- near repdigit
  - AA..AAB
  - ABB..BB
  - AA..AABA
  - ABAA..AA
- near repdigit related
  - plateau ABB..BBA, B > A
  - depression ABB..BBA, B < A
  - quasi ABB..BBC (A != C)
  - palindrome AA..AABAA..AA
- cyclotomic numbers

# ideas from factordb.com

- cullen numbers (n\*2^n+1)
- woodall numbers (n\*2^n-1)
- cunningham numbers (b^n+1 and b^n-1)
- near-cunningham (k\*b^n+d and k\*b^n-d)
- generalized hyper-cullen (x^y\*y^x+1)
- generalized hyper-woodall (x^y\*y^x-1)
- near-cullen ((n-1)\*2^n+1 and (n+1)\*2^n+1)
- near-woodall ((n-1)\*2^n-1 and (n+1)\*2^n-1)
- n! - n - 1
- n! + n + 1
- x^y + y^x
- x^y - y^x

# ideas from y-cruncher

- golden ratio
- square/cube/4th/... roots of integers
- log(2), log(3), ...
- zeta(2), zeta(3), ...
- catalan constant
- euler-mascheroni constant
- plastic ratio
- bronze ratio
- silver ratio
- metallic means
- supergolden ratio
- sin(1), cos(1)
- trigonometric functions and inverses
- gamma function
- dirichlet function
- erf(1)
- lemniscate
- unnormalized fresnel
- weierstrass constant
- i^i (imaginary unit)
- euler-gompertz constant
- heeger numbers
- khinchin-levy constant
- levy constant
- log(pi)
- log10(2)
- psi constant
- plastic number
- ramanujan number
- sierpinski constant
- universal parabolic constant
- airy function
- constants for differential equations
- constants for various integrals
- other powers of pi
- other powers of e
- e^(-e)
- e^(1/e)
- e^e
- e^pi
- pi^pi
- pi^pi^pi
- pi^e
