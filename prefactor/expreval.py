import bases
import primes
import sequences

exprfuncs = {

    # bases
    'to_base': bases.toBase,
    'to_factorial_base': bases.toFactorialBase,
    'from_base': bases.fromBase,
    'from_factorial_base': bases.fromFactorialBase,

    # primes
    'nth_prime': primes.nthPrime,
    'nth_composite': primes.nthComposite,

    # common sequences
    'fibonacci': sequences.fibonacci,
    'lucas': sequences.lucas,
    'factorial': sequences.factorial,
    'primorial': sequences.primorial,
    'compositorial': sequences.compositorial,
    'lucas_u': sequences.lucasU,
    'lucas_v': sequences.lucasV,
    'mersenne': sequences.mersenne,
    'fermat': sequences.fermat,

    # repunit and functions for several bases
    'repunit': sequences.repunit,
    **{
        f'repunit{b}': lambda n : sequences.repunit(b,n)
        for b in range(2,36+1)
    },

    # repdigit related
    'near_repdigit': sequences.nearRepdigit,
    **{
        f'near_repdigit{b}': lambda p,n : sequences.nearRepdigit(b,p,n)
        for b in range(2,36+1)
    },

    # other sequences (similar to fibonacci)
    'padovan': sequences.padovan,
    'perrin': sequences.perrin,
    'vanderlaan': sequences.vanderlaan,
    'narayana': sequences.narayana,
    'jacobsthal': sequences.jacobsthal,
    'jacobsthal_lucas': sequences.jacobsthal_lucas,
    'pell': sequences.pell,
    'pell_lucas': sequences.pell_lucas,

    # generalized fermat
    'gfermat1': sequences.gfermat1,
    'gfermat2': sequences.gfermat2,

    # multiple factorial
    'double_factorial': lambda n : sequences.multiFactorial(2,n),
    'triple_factorial': lambda n : sequences.multiFactorial(3,n),
    'multi_factorial': sequences.multiFactorial,
}

def expreval(expr:str,n:int) -> int:
    ret = eval(expr.replace('{}',repr(n)),exprfuncs)
    assert isinstance(ret,int)
    return ret

if __name__ == '__main__':

    def seqcmp(expr:str,i:int,j:int,seq:list[int]):
        seq2 = [expreval(expr,k) for k in range(i,j)]
        assert len(seq) == len(seq2)
        for k in range(i,j):
            assert seq[k-i] == seq2[k-i], f'{expr} n={k} expected {seq[k-i]} actual {seq2[k-i]}'

    seqcmp('nth_prime({})',1,10,[2,3,5,7,11,13,17,19,23])
    seqcmp('nth_composite({})',1,10,[4,6,8,9,10,12,14,15,16])

    seqcmp('fibonacci({})',0,15,[0,1,1,2,3,5,8,13,21,34,55,89,144,233,377])
    seqcmp('lucas({})',0,15,[2,1,3,4,7,11,18,29,47,76,123,199,322,521,843])
    seqcmp('factorial({})',0,10,[1,1,2,6,24,120,720,5040,40320,362880])
    seqcmp('primorial({})',1,12,[1,2,6,6,30,30,210,210,210,210,2310])
    seqcmp('compositorial({})',1,12,[1,1,1,4,4,24,24,192,1728,17280,17280])
    seqcmp('mersenne({})',1,10,[3,7,31,127,2047,8191,131071,524287,8388607])
    seqcmp('fermat({})',0,6,[3,5,17,257,65537,4294967297])

    seqcmp('repunit(2,{})',0,10,[0,1,3,7,15,31,63,127,255,511])
    seqcmp('repunit(10,{})',0,10,[0,1,11,111,1111,11111,111111,1111111,11111111,111111111])
    seqcmp('near_repdigit(10,"12*3",{})',0,5,[13,123,1223,12223,122223])
    seqcmp('near_repdigit(10,"9*89*",{})',0,5,[8,989,99899,9998999,999989999])

    seqcmp('double_factorial({})',0,12,[1,1,2,3,8,15,48,105,384,945,3840,10395])
    seqcmp('triple_factorial({})',0,12,[1,1,2,3,4,10,18,28,80,162,280,880])
    seqcmp('multi_factorial(4,{})',0,12,[1,1,2,3,4,5,12,21,32,45,120,231])

    seqcmp('padovan({})',0,15,[1,1,1,2,2,3,4,5,7,9,12,16,21,28,37])
    seqcmp('perrin({})',0,15,[3,0,2,3,2,5,5,7,10,12,17,22,29,39,51])
    seqcmp('vanderlaan({})',0,15,[1,0,1,1,1,2,2,3,4,5,7,9,12,16,21])
    seqcmp('narayana({})',0,15,[1,1,1,2,3,4,6,9,13,19,28,41,60,88,129])
    # vanderlaan is padovan offset, less known it seems
    # narayana is for the cow sequence, not the combinatorics triangle

    seqcmp('jacobsthal({})',0,10,[0,1,1,3,5,11,21,43,85,171]) # (2^n-(-1)^n)/3
    # alternative jacobsthal recurrence: J(n+1)=2*J(n)+(-1)^n, J(n+1)=2^n-J(n)
    seqcmp('jacobsthal_lucas({})',0,10,[2,1,5,7,17,31,65,127,257,511]) # 2^n+(-1)^n
    # alternative jacobsthal-lucas recurrence: j(n+1)=2*j(n)-3*(-1)^n
    seqcmp('pell({})',0,10,[0,1,2,5,12,29,70,169,408,985])
    seqcmp('pell_lucas({})',0,10,[2,2,6,14,34,82,198,478,1154,2786])

    seqcmp('gfermat1(2,{})',0,5,[3,5,17,257,65537])
    seqcmp('gfermat1(3,{})',0,5,[2,5,41,3281,21523361])
    seqcmp('gfermat2(2,1,{})',0,5,[3,5,17,257,65537])
    seqcmp('gfermat2(3,1,{})',0,5,[2,5,41,3281,21523361])
    seqcmp('gfermat2(3,2,{})',0,5,[5,13,97,6817,43112257])
