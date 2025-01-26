#!/bin/bash
git clone https://gitlab.inria.fr/zimmerma/ecm
cd ecm
autoreconf -i
./configure
make -j8
cd ..
gcc trial_div.c -O3 -g -Wall -Werror -Wextra -lgmp -o tdiv
gcc pollard_rho.c -O3 -g -Wall -Werror -Wextra -lgmp -o prho
