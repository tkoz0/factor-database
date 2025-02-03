'''
prefactoring numbers before adding them to the database

requires
- tdiv, see trial_div.c
- prho, see pollard_rho.c
- ecm, see https://gitlab.inria.fr/zimmerma/ecm

1. trial division up to 10^5 (all factors up to 5 digits will be found)
2. pollard rho for 10^6 iterations (high chance to find factors up to 12 digits)
3. ecm b1=2000, 2000 curves (very high chance to find smaller factors)
4. ecm b1=10000, 1000 curves (high chance to find factors up to 20 digits)
5. ecm b1=50000, 500 curves (moderate chance to find factors up to 25 digits)
'''

# =======
# imports
# =======

import math
import multiprocessing
import os
import random
import re
import select
import subprocess
from time import time,sleep
from tqdm import tqdm
import sys

import gmpy2

# ==========
# parameters
# ==========

debug = False

script_dir = os.path.dirname(__file__)
path_tdiv = f'{script_dir}/tdiv'
path_prho = f'{script_dir}/prho'
path_ecm = f'{script_dir}/ecm/ecm'

# ==========
# ecm runner
# ==========

using_re = re.compile(r'Using B1=(\d+), B2=(\d+), polynomial (.+), sigma=(.+)')
factor_re = re.compile(r'Found (prime|composite) factor of \d+ digits: (\d+)')
cofactor_re = re.compile(r'(Prime|Composite) cofactor (\d+) has \d+ digits')

def ecm_runner(n:int,
               curves:int,
               b1:int,
               b2:int|None=None,
               threads:int=0,
               maxmem:int|None=None,
               output:list[list[str]]|None=None,
               progress_stream=None) \
                -> tuple[int,int,int]:
    '''
    manages parallel execution of ecm until a single factor is found
    TODO does not properly handle unexpected subprocess termination
    returns (factor1,factor2,curves_run)
    '''
    if threads <= 0:
        threads = (multiprocessing.cpu_count()+1)//2
    if debug:
        threads = 1
        progress_stream = sys.stderr
    assert threads > 0
    assert curves > 0
    assert output is None or output == []
    cmd = [path_ecm,'-c','0','-one']
    if maxmem is not None:
        cmd.append('-maxmem')
        cmd.append(str(maxmem))
    cmd.append(str(b1))
    if b2 is not None:
        cmd.append(str(b2))

    # track info for each subprocess
    procs: list[subprocess.Popen] = []
    procs_poll = select.epoll(threads)
    procs_fds = dict() # fdnum -> stream,proc_index
    last_line: list[str] = []
    last_stage: list[int] = []
    last_b1: list[int] = []
    last_b2: list[int] = []
    last_poly: list[str] = []
    last_sigma: list[str] = []

    # initialize
    t_start = time()
    t_sleep = math.sqrt(b1/threads) * 1e-4
    for ii in range(threads):
        procs.append(subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1 # line buffered
        ))

        # stdout polling
        assert procs[-1].stdout
        procs_poll.register(procs[-1].stdout,select.EPOLLIN)
        fd = procs[-1].stdout.fileno()
        procs_fds[fd] = (procs[-1].stdout,ii)

        # write number to stdin
        assert procs[-1].stdin
        procs[-1].stdin.write(str(n))
        procs[-1].stdin.flush()
        procs[-1].stdin.close()

        # add list element corresponding to process
        if output is not None:
            output.append([])
        last_line.append('')
        last_stage.append(0)
        last_b1.append(0)
        last_b2.append(0)
        last_poly.append('')
        last_sigma.append('')

    # monitor output
    found_factor = None
    found_cofactor = None
    found_index = None
    completed_curves = 0
    threads_running = threads
    if progress_stream is not None:
        progress_tqdm = tqdm(range(curves),file=progress_stream)
        progress_iter = iter(progress_tqdm)
    else:
        progress_iter = iter(range(curves))
    while completed_curves < curves:
        any_change = False
        done = False

        # check ready outputs
        for fdnum,_ in procs_poll.poll(0):
            stream,i = procs_fds[fdnum]

            any_change = True
            line: str = stream.readline()
            if not line: # eof
                continue
            last_line[i] += line
            if not last_line[i].endswith('\n'): # need more from buffer
                continue
            line = last_line[i]
            last_line[i] = ''
            if output:
                output[i].append(line)
            if debug:
                progress_tqdm.write(line,end='')

            if line.startswith('Run'): # starting new curve
                completed_curves += 1
                next(progress_iter)
                if completed_curves + threads_running > curves:
                    procs[i].terminate()
                    threads_running -= 1
                    # TODO this also needs to be decremented on unexpected subprocess termination
                if completed_curves >= curves:
                    break

            elif line.startswith('Using'): # parameters
                match = using_re.match(line)
                assert match is not None, f'unexpected line: {repr(line)}'
                s_b1,s_b2,s_poly,s_sigma = match.groups()
                last_b1[i] = int(s_b1)
                last_b2[i] = int(s_b2)
                last_poly[i] = s_poly
                last_sigma[i] = s_sigma

            elif line.startswith('Step 1'):
                last_stage[i] = 1

            elif line.startswith('Step 2'):
                last_stage[i] = 2

            elif line.startswith('****'): # factored
                if progress_stream is not None:
                    progress_tqdm.close()
                for line in procs[i].stdout: # type:ignore
                    if output:
                        output[i].append(line)
                    if debug:
                        print(line)
                    m1 = factor_re.match(line)
                    m2 = cofactor_re.match(line)
                    if m1:
                        status,value = m1.groups()
                        found_factor = (int(value), status == 'prime')
                        found_index = i
                    if m2:
                        status,value = m2.groups()
                        found_cofactor = (int(value), status == 'Prime')
                        found_index = i

                completed_curves += 1
                next(progress_iter)
                if isinstance(found_index,int):
                    done = True
                    break

        if done:
            break

        if not any_change:
            sleep(t_sleep)

    for proc in procs:
        proc.terminate()

    try:
        next(progress_iter)
    except:
        pass

    t_finish = time()
    if progress_stream is not None:
        progress_stream.write(f'completed {completed_curves} curves in {t_finish-t_start:.3f} sec\n')

    if found_index is None:
        return (0,0,completed_curves)

    assert found_factor is not None
    assert found_cofactor is not None

    i = found_index
    if progress_stream is not None:
        progress_stream.write(f'stage={last_stage[i]},b1={last_b1[i]},b2={last_b2[i]},poly={last_poly[i]},sigma={last_sigma[i]}\n')
        progress_stream.write(f'factor {found_factor}\n')
        progress_stream.write(f'cofactor {found_cofactor}\n')

    return (found_factor[0],found_cofactor[0],completed_curves)

# ============
# prefactoring
# ============

def prp(n:int) -> bool:
    return gmpy2.is_prime(n,50) # type:ignore

def prefactor_runner(n:int,
                     lim_tdiv:int=0,
                     lim_prho:int=0,
                     ecm_b1_curves:tuple[tuple[int,int],...]=(),
                     ecm_threads:int=0,
                     progress_stream=None) -> list[tuple[int,bool,str]]:
    '''
    apply prefactoring steps to number and get a list of (factor,primality,algo)
    primality is a probable test from gmpy2.is_prime
    algo is the algorithm used from ('tdiv','prho','ecm')
    '''
    assert n > 1
    cofactor = n
    factors: list[tuple[int,bool,str]] = []

    # trial division finds all factors below chosen limit
    if lim_tdiv > 0:

        if progress_stream:
            progress_stream.write(f'running tdiv on {cofactor}\n')
        t = time()
        proc_tdiv = subprocess.Popen(
            [path_tdiv,str(lim_tdiv),str(cofactor)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        assert proc_tdiv.stdout
        for line in proc_tdiv.stdout:
            f = int(line)
            assert prp(f)
            factors.append((f,True,'tdiv'))
            assert cofactor % f == 0
            cofactor //= f
        if progress_stream:
            if len(factors):
                progress_stream.write(f'found factors {','.join(str(f) for f,_,_ in factors)} with trial division ({time()-t:.3f} sec)\n')
            else:
                progress_stream.write(f'no factor found ({time()-t:.3f} sec)\n')

    # attempt pollard rho until it fails to find a factor in iteration limit
    if lim_prho > 0:

        cofactors_attempt: list[int] = []
        if cofactor > 1:
            cofactors_attempt.append(cofactor)
        cofactors_done: list[int] = []
        while len(cofactors_attempt) > 0:
            # get a cofactor, nothing to do if it is prime
            cofactor = cofactors_attempt.pop()
            if prp(cofactor):
                factors.append((cofactor,True,'prho'))
                continue

            # iteration with some randomly chosen parameters
            x0 = 2 + random.getrandbits(8)
            b = 1 + random.getrandbits(8)
            if progress_stream:
                progress_stream.write(f'running prho on {cofactor}\n')
            t = time()
            proc_prho = subprocess.Popen(
                [path_prho,str(lim_prho),str(x0),str(b),str(cofactor)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            assert proc_prho.stdout
            line = proc_prho.stdout.readline()
            if not line: # did not find factor
                if progress_stream:
                    progress_stream.write(f'no factor found ({time()-t:.3f} sec)\n')
                cofactors_done.append(cofactor)
                continue

            f = int(line)
            assert 1 < f < cofactor
            assert cofactor % f == 0
            if progress_stream:
                progress_stream.write(f'found factor {f} with prho ({time()-t:.3f} sec)\n')
            cofactors_attempt.append(f)
            cofactors_attempt.append(cofactor//f)

    # attempt ecm until it fails to find factor with all parameter choices
    cofactors_attempt = cofactors_done
    cofactors_done = []
    while len(cofactors_attempt) > 0:
        # get a cofactor, nothing to do if it is prime
        cofactor = cofactors_attempt.pop()
        if prp(cofactor):
            factors.append((cofactor,True,'ecm'))
            continue

        # ecm using selected parameter choices
        f1,f2,num_curves = 0,0,0
        for b1,curves in ecm_b1_curves:
            t = time()
            if progress_stream:
                progress_stream.write(f'running ecm with b1={b1} for {curves} curves on {cofactor}\n')
            f1,f2,num_curves = ecm_runner(cofactor,curves,b1,threads=ecm_threads,progress_stream=progress_stream)
            if f1 != 0:
                break

        if f1 == 0: # no factor found
            if progress_stream:
                progress_stream.write(f'no factor found ({time()-t:.3f} sec)\n')
            cofactors_done.append(cofactor)
            continue

        assert f2 != 0
        assert num_curves > 0
        assert f1 and f2
        assert 1 < f1 < cofactor
        assert 1 < f2 < cofactor
        assert cofactor % f1 == 0
        assert cofactor % f2 == 0
        assert f1 * f2 == cofactor
        if progress_stream:
            progress_stream.write(f'found factor {f1} with ecm using b1={b1} and {num_curves} curves ({time()-t:.3f} sec)\n')
        cofactors_attempt.append(f1)
        cofactors_attempt.append(f2)

    # after this would be snfs/gnfs if choosing to implement further factoring
    for f in cofactors_done:
        factors.append((f,prp(f),'ecm'))

    return sorted(factors)

# ===========
# test runner
# ===========

# factoring parameters
lim_tdiv = 10**5
lim_prho = 10**6
ecm_b1_curves = ((2000,2000),(10000,1000),(50000,500))

if __name__ == '__main__':

    nums = map(int,sys.stdin)

    for i,n in enumerate(nums):
        print(f'\033[94mFACTORING INPUT {i}\033[0m',file=sys.stderr)
        if n < 2:
            print(f'small number {n}',file=sys.stderr)
        else:
            ret = prefactor_runner(n,lim_tdiv,lim_prho,ecm_b1_curves,0,sys.stderr)
            all_prime = all(p for _,p,_ in ret)
            for f,p,a in ret:
                assert p == prp(f)
            if all_prime:
                status = '\033[32mCOMPLETELY FACTORED\033[0m'
            elif len(ret) > 1:
                status = '\033[33mPARTIALLY FACTORED\033[0m'
            else:
                status = '\033[31mNO FACTORS FOUND\033[0m'
            print(f'INPUT {i} {n}',file=sys.stderr)
            for f in ret:
                print(f,file=sys.stderr)
            print(status,file=sys.stderr)
        print(file=sys.stderr)
