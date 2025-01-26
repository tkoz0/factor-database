#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <gmp.h>

bool prho_gmp(mpz_t N, uint64_t IT, uint64_t X0, uint64_t B)
{
    assert(mpz_cmp_ui(N,65535) > 0);
    mpz_t X;
    mpz_t Y;
    mpz_t D;
    mpz_t A;
    mpz_t Q;
    mpz_t ZX;
    mpz_t ZY;
    mpz_init(X);
    mpz_init(Y);
    mpz_init(D);
    mpz_init(A);
    mpz_init(Q);
    mpz_init(ZX);
    mpz_init(ZY);
    mpz_set_ui(X,X0);
    mpz_set_ui(Y,X0);
    mpz_set_ui(D,1);
    mpz_set_ui(Q,1);
    while (IT != 0)
    {
        mpz_set(ZX,X);
        mpz_set(ZY,Y);
        uint64_t IT0 = 100;
        while (IT0 > 0 && IT > 0)
        {
            mpz_mul(X,X,X);
            mpz_add_ui(X,X,B);
            mpz_mod(X,X,N);
            mpz_mul(Y,Y,Y);
            mpz_add_ui(Y,Y,B);
            mpz_mod(Y,Y,N);
            mpz_mul(Y,Y,Y);
            mpz_add_ui(Y,Y,B);
            mpz_mod(Y,Y,N);
            mpz_sub(A,X,Y);
            mpz_mul(Q,Q,A);
            mpz_mod(Q,Q,N);
            --IT0;
            --IT;
        }
        mpz_gcd(D,Q,N);
        if (mpz_cmp_ui(D,1) != 0)
            break;
    }
    if (mpz_cmp(D,N) == 0)
    {
        for (;;)
        {
            mpz_mul(ZX,ZX,ZX);
            mpz_add_ui(ZX,ZX,B);
            mpz_mod(ZX,ZX,N);
            mpz_mul(ZY,ZY,ZY);
            mpz_add_ui(ZY,ZY,B);
            mpz_mod(ZY,ZY,N);
            mpz_mul(ZY,ZY,ZY);
            mpz_add_ui(ZY,ZY,B);
            mpz_mod(ZY,ZY,N);
            mpz_sub(A,ZX,ZY);
            mpz_gcd(D,A,N);
            if (mpz_cmp_ui(D,1) != 0)
                break;
        }
    }
    bool R = mpz_cmp_ui(D,1) != 0 && mpz_cmp(D,N) != 0;
    if (R)
        gmp_printf("%Zd\n",D);
    mpz_clear(X);
    mpz_clear(Y);
    mpz_clear(D);
    mpz_clear(A);
    mpz_clear(Q);
    mpz_clear(ZX);
    mpz_clear(ZY);
    return R;
}

// prho <iters> <init> <add> <number>
int main(int argc, char **argv)
{
    assert(argc == 5);
    mpz_t N;
    mpz_init(N);
    mpz_set_str(N,argv[4],10);
    prho_gmp(N,atoll(argv[1]),atoll(argv[2]),atoll(argv[3]));
    mpz_clear(N);
    return 0;
}
