#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <gmp.h>

void tdiv_gmp(mpz_t N, uint64_t L)
{
    assert(L <= 4294967291ull);
    assert(mpz_cmp_ui(N,0) > 0);
    mpz_t Q;
    mpz_init(Q);
    uint64_t R;
    while (mpz_even_p(N))
    {
        mpz_div_2exp(N,N,1);
        printf("2\n");
    }
    while ((R = mpz_div_ui(Q,N,3)) == 0)
    {
        mpz_set(N,Q);
        printf("3\n");
    }
    while ((R = mpz_div_ui(Q,N,5)) == 0)
    {
        mpz_set(N,Q);
        printf("5\n");
    }
    uint64_t D = 5;
    for (;;)
    {
        D += 2;
        if (D > L)
            break;
        while ((R = mpz_div_ui(Q,N,D)) == 0)
        {
            mpz_set(N,Q);
            printf("%lu\n",D);
        }
        D += 4;
        if (D > L)
            break;
        while ((R = mpz_div_ui(Q,N,D)) == 0)
        {
            mpz_set(N,Q);
            printf("%lu\n",D);
        }
    }
    mpz_clear(Q);
}

// tdiv <limit> <number>
int main(int argc, char **argv)
{
    assert(argc == 3);
    uint64_t L = atoll(argv[1]);
    mpz_t N;
    mpz_init(N);
    mpz_set_str(N,argv[2],10);
    tdiv_gmp(N,L);
    mpz_clear(N);
    return 0;
}
