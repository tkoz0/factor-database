#!/bin/bash
git clone https://gitlab.inria.fr/zimmerma/ecm
cd ecm
autoreconf -i
./configure
make -j8
cd ..
gcc tdiv.c -O3 -g -Wall -Werror -Wextra -lgmp -o tdiv
gcc prho.c -O3 -g -Wall -Werror -Wextra -lgmp -o prho
