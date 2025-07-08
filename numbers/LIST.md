# fdb.tkoz.me production list

- Fibonacci
  - $ F_0=0, F_1=1, F_n=F_{n-1}+F_{n-2} $
  - indexes 0-4999 (max 1045 digit / 3470 bit)
- Lucas
  - $ L_0=2, L_1=1, L_n=L_{n-1}+L_{n-2} $
  - indexes 0-4999 (max 1045 digit / 3471 bit)
- Repunits
  - bases $ 2 \leq b \leq 36 $, terms $ (b^n-1)/(b-1) $ where $ n \geq 0 $
  - indexes 0-999 for each base
  - (base 2 max 301 digit / 999 bit)
  - (base 10 max 999 digit / 3316 bit)
  - (base 36 max 1554 digit / 5160 bit)

# fdb.tkoz.me production plan

- Factorial and related
  - Factorial: $ n!-1, n!+1 $
  - Double factorial: $ n!!-1, n!!+1 $
  - Triple factorial: $ n!!!-1, n!!!+1 $
  - Primorial: $ n\#-1, n\#+1 $
  - Compositorial: $ n!/n\#-1, n!/n\#+1 $

- Repunit and related
  - Repunits, bases $ > 36 $
  - Negative base repunits, bases $ -2 \geq b \geq -36 $
    - possibly more bases
  - Near repdigit related
    - see more details on stdkmd.net/nrr
    - near-repdigit: AA..AAB, ABB..BB, AA..AABA, ABAA..AA
    - plateau/depression: ABB..BBA
    - quasi-repdigit: ABB..BBC
    - palindrome: AA..AABAA..AA
