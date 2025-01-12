import quart
import math

import app.database
from app.database import Primality
from app.config import ADMIN_EMAIL

def getSession(token:str|None = None) -> app.database.SessionRow|None:
    '''
    returns the session based on the token
    gets token from cookie if not specified
    '''
    if token is None:
        token = quart.request.cookies.get('token')
    if token is None:
        return None
    try:
        token_bytes = bytes.fromhex(token)
    except:
        return None # invalid token format
    return app.database.getSession(token_bytes)

def getUser(user:str|int|None = None) -> app.database.UserRow|None:
    '''
    returns the user based on the token cookie, or from username/email/id
    '''
    if user is None:
        session = getSession()
        if session is None:
            return None
        return app.database.getUser(session.user_id)
    return app.database.getUser(user)

# logged in
pages_header_user = [('home','/'),('tables','/tables'),('account','/account')]
pages_footer_user = [('about','/about'),('privacy','/privacy')]

# not logged in
pages_header_anon = [('home','/'),('tables','/tables'),
                     ('login','/login'),('signup','/signup')]
pages_footer_anon = [('about','/about'),('privacy','/privacy')]

# TODO pages that have not been implemented yet
# removed from header: ('recent','/recent') and ('stats','/stats')
# removed from footer: ('guide','/guide') and ('api','/api')

def getPageInfo(token:str|None = None):
    '''
    returns details used to render page templates
    token may be provided, otherwise it comes from cookie
    '''
    session = getSession(token)

    if session is None: # not logged in
        return {
            'remote_addr': quart.request.remote_addr,
            'logged_in': False,
            'headlinks': pages_header_anon,
            'footlinks': pages_footer_anon,
            'admin_email': ADMIN_EMAIL
        }

    else: # logged in
        user = getUser(session.user_id)
        assert user is not None, 'internal error'
        return {
            'remote_addr': quart.request.remote_addr,
            'logged_in': True,
            'username': user.username,
            'email': user.email,
            'fullname': user.username if user.fullname == '' else user.fullname,
            'is_admin': user.is_admin,
            'is_disabled': user.is_disabled,
            'headlinks': pages_header_user,
            'footlinks': pages_footer_anon,
            'admin_email': ADMIN_EMAIL,
            'sess_exp': session.expires.replace(microsecond=0)
        }

_f_open = {
    Primality.UNKNOWN: '{',
    Primality.COMPOSITE: '[',
    Primality.PROBABLE: '(',
    Primality.PRIME: ''
}

_f_close = {
    Primality.UNKNOWN: '}',
    Primality.COMPOSITE: ']',
    Primality.PROBABLE: ')',
    Primality.PRIME: ''
}

_f_class = {
    Primality.UNKNOWN: 'factor_unknown',
    Primality.COMPOSITE: 'factor_comp',
    Primality.PROBABLE: 'factor_prob',
    Primality.PRIME: 'factor_prime'
}

def makeFactorsHTML(factors:list[tuple[int,int,None|int]]) -> str:
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

def makeSmallFactorsHTML(fs:list[int]|tuple[int,...]):
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

async def blank400(msg:str):
    return quart.Response(
        await quart.render_template('400.jinja',msg=msg),400)

async def blank401(msg:str):
    return quart.Response(
        await quart.render_template('401.jinja',msg=msg),401)

async def blank403(msg:str):
    return quart.Response(
        await quart.render_template('403.jinja',msg=msg),403)

async def blank404(msg:str):
    return quart.Response(
        await quart.render_template('404.jinja',msg=msg),404)
