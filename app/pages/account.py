import quart

import app.database.users as dbUser
from app.database.helpers import FdbException

from app.utils.pageData import basePageData
from app.utils.session import getSession
from app.config import RENEW_SESSIONS

bp = quart.Blueprint('account',__name__)

@bp.get('/login')
async def loginGet():
    '''
    login form page
    '''
    return await quart.render_template('login_form.jinja',
                                       page='login',
                                       **basePageData())

@bp.post('/login')
async def loginPost():
    '''
    login attempt by post request
    '''
    data = await quart.request.form
    code = 200
    ok = False
    ip = quart.request.remote_addr
    token: None|str = None

    if 'username' in data and 'password' in data:

        u,p = data['username'],data['password']
        assert isinstance(u,str) and isinstance(p,str), 'internal error'
        user = dbUser.verifyUser(u,p,quart.request.remote_addr)

        if user is not None:

            if user.is_disabled:
                msg = 'Your account is disabled.'
                code = 403

            else:
                assert user.username is not None, 'internal error'
                token = dbUser.createSession(user.username,ip)
                msg = 'Login successful.'
                ok = True

        else:
            msg = 'Invalid login.'
            code = 401

    else:
        msg = f'Malformed login request.'
        code = 400

    ret = quart.Response(
        await quart.render_template('login_post.jinja',
                                    page='login',
                                    post_ok=ok,
                                    post_msg=msg,
                                    **basePageData(token)),
        code)

    if token is not None:
        session = getSession(token)
        assert session is not None, 'internal error'
        ret.set_cookie('token',token,expires=session.expires)

    return ret

@bp.get('/account')
async def accountGet():
    '''
    account details page
    '''
    session = getSession()
    token = None
    new_sess_exp = None
    exp_time = None

    if session is not None: # user logged in
        exp_time = session.expires.replace(microsecond=0)
        try:
            token = quart.request.cookies.get('token')
            assert token is not None, 'internal error'
            token_bytes = bytes.fromhex(token)
            ip = quart.request.remote_addr
            if RENEW_SESSIONS:
                exp_time = dbUser.updateSession(token_bytes,ip) \
                    .replace(microsecond=0)
        except:
            pass

    ret = quart.Response(
        await quart.render_template('account.jinja',
                                    page='account',
                                    exp_time=exp_time,
                                    **basePageData()))

    if token is not None:
        ret.set_cookie('token',token,expires=new_sess_exp)

    return ret

@bp.post('/account')
async def accountPost():
    '''
    post request to make changes to account
    '''
    data = await quart.request.form
    code = 200
    session = getSession()
    ok = False
    key = None

    if session is None:
        msg = 'You are not logged in.'

    elif 'password' in data and 'new_password' in data \
            and 'verify_password' in data:

        if len(data['new_password']) > 128 \
                or len(data['verify_password']) > 128:
            msg = 'Maximum password length is 128 characters.'
            code = 400

        elif data['new_password'] != data['verify_password']:
            msg = 'New passwords do not match.'
            code = 400

        else:

            try:
                dbUser.changeUserPassword(session.user_id,
                                          data['new_password'],
                                          data['password'])
                msg = 'Password updated.'
                ok = True

            except FdbException as e:
                msg = str(e)
                ok = False
                code = 400

    elif 'api' in data and data['api'] == '1':

        user_row = dbUser.getUser(session.user_id)
        assert user_row is not None, 'internal error'
        key = dbUser.makeApiKey(session.user_id)
        msg = f'API key generated. Please save it securely.'
        ok = True

    else:
        msg = 'Malformed request.'
        code = 400

    if key is not None:
        key = key.hex()

    return quart.Response(
        await quart.render_template('account.jinja',page='account',
                                    post_ok=ok,post_msg=msg,api_key=key,
                                    **basePageData()),code)

@bp.route('/signup')
async def signup():
    '''
    signup page
    '''
    return await quart.render_template('signup.jinja',page='signup',
                                       **basePageData())

@bp.route('/logout')
async def logout():
    '''
    logout user
    '''
    token = quart.request.cookies.get('token')
    try:
        token_bytes = bytes.fromhex(token) # type:ignore
        dbUser.deleteSession(token_bytes)
    except:
        pass
    ret = quart.Response(
        await quart.render_template('logout.jinja',page='logout',
                                    **basePageData()))
    ret.delete_cookie('token')
    return ret
