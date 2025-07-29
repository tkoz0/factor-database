import math

from app.database import Primality

# opening bracket to use
_f_open = {
    Primality.UNKNOWN: '{',
    Primality.COMPOSITE: '[',
    Primality.PROBABLE: '(',
    Primality.PRIME: ''
}

# closing bracket to use
_f_close = {
    Primality.UNKNOWN: '}',
    Primality.COMPOSITE: ']',
    Primality.PROBABLE: ')',
    Primality.PRIME: ''
}

# css class by primality status
_f_class = {
    Primality.UNKNOWN: 'factor_unknown',
    Primality.COMPOSITE: 'factor_comp',
    Primality.PROBABLE: 'factor_prob',
    Primality.PRIME: 'factor_prime'
}

def factorsHtml(factors:list[tuple[int,int,None|int]]) -> str:
    '''
    generate the html for displaying a factorization
    '''
    # generating in python instead of jinja because of the '&times;'.join()
    data = []

    mdict: dict[int,int] = {}
    vdict: dict[int,tuple[int,int|None]] = {}
    for factor,primality,f_id in factors:
        if factor not in mdict:
            mdict[factor] = 0
        mdict[factor] += 1
        vdict[factor] = (primality,f_id)

    for factor in mdict:
        primality,f_id = vdict[factor]
        multiplicity = mdict[factor]
        f_str = str(factor)
        f_len = len(f_str)
        f_open = _f_open[primality]
        f_close = _f_close[primality]
        f_class = _f_class[primality]
        multstr = f'<sup>{multiplicity}</sup>' \
                    if multiplicity > 1 else ''
        lenstr = f'<sub>&lt;{f_len}&gt;</sub>' \
                    if factor.bit_length() > 32 else ''
        if f_id is None:
            data.append(f'<span class="small_factor">{factor}'
                        f'{multstr}{lenstr}</span>')
        else:
            data.append(f'{f_open}<a href="/factor/{f_id}" '
                        f'class="factor_link {f_class}"'
                        f'>{f_str}</a>{multstr}{lenstr}{f_close}')

    return ' &times;\n'.join(data)

def smallFactorsHtml(fs:list[int]|tuple[int,...]) -> str:
    '''
    string for displaying small factors
    '''
    data: dict[int,int] = {}
    for f in fs:
        if f not in data:
            data[f] = 0
        data[f] += 1
    strs: list[str] = []
    for f in data:
        f_str = str(f)
        f_len = len(f_str)
        strs.append(f_str)
        m = data[f]
        if m > 1:
            strs[-1] += f'<sup>{m}</sup>'
        if f.bit_length() > 32:
            strs[-1] += f'<sub>&lt;{f_len}&gt;</sub>'
    return ' &times; '.join(strs)

_prog_prime = (Primality.PROBABLE,Primality.PRIME)
_prog_log = lambda x : math.log(x)

def factoringProgress(n:int,fs:list[tuple[int,int,int|None]]) -> float:
    '''
    return factoring progress as a ratio of log(factored part) / log(n)
    '''
    return sum(_prog_log(f) for f,p,_ in fs if p in _prog_prime) / _prog_log(n)
