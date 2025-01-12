import quart

import app.database
import app.util

bp = quart.Blueprint('account',__name__)

@bp.get('/login')
async def login_form():
    return await quart.render_template('login_form.jinja',page='login',
                                       **app.util.getPageInfo())

@bp.post('/login')
async def login_post():
    data = await quart.request.form
    code = 200
    ok = False
    ip = quart.request.remote_addr
    token: None|str = None

    if 'username' in data and 'password' in data:

        u,p = data['username'],data['password']
        assert isinstance(u,str) and isinstance(p,str), 'internal error'
        user = app.database.verifyUser(u,p,quart.request.remote_addr)

        if user is not None:

            if user.is_disabled:
                msg = 'Your account is disabled.'
                code = 403

            else:
                assert user.username is not None, 'internal error'
                token = app.database.createSession(user.username,ip)
                msg = 'Login successful.'
                ok = True

        else:
            msg = 'Invalid login.'
            code = 401

    else:
        msg = f'Malformed login request.'
        code = 400

    ret = quart.Response(
        await quart.render_template('login_post.jinja',page='login',
                                    post_ok=ok,post_msg=msg,
                                    **app.util.getPageInfo(token)),code)
    if token is not None:
        session = app.util.getSession(token)
        assert session is not None, 'internal error'
        ret.set_cookie('token',token,expires=session.expires)
    return ret

@bp.get('/account')
async def account_page():
    session = app.util.getSession()
    token = None
    new_sess_exp = None
    if session is not None:
        try:
            token = quart.request.cookies.get('token')
            assert token is not None, 'internal error'
            token_bytes = bytes.fromhex(token)
            ip = quart.request.remote_addr
            new_sess_exp = app.database.updateSession(token_bytes,ip)
            new_sess_exp = new_sess_exp.replace(microsecond=0)
        except:
            pass
    ret = quart.Response(
        await quart.render_template('account.jinja',page='account',
                                    new_sess_exp=new_sess_exp,
                                    **app.util.getPageInfo()))
    if token is not None:
        ret.set_cookie('token',token,expires=new_sess_exp)
    return ret

@bp.post('/account')
async def account_post():
    data = await quart.request.form
    code = 200
    session = app.util.getSession()
    ok = False

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
                app.database.changeUserPassword(session.user_id,
                                                data['new_password'],
                                                data['password'])
                msg = 'Password updated.'
                ok = True

            except app.database.FDBException as e:
                msg = str(e)
                ok = False
                code = 400

    else:
        msg = 'Malformed password change request.'
        code = 400

    return quart.Response(
        await quart.render_template('account.jinja',page='account',
                                    post_ok=ok,post_msg=msg,
                                    **app.util.getPageInfo()),code)

@bp.route('/signup')
async def signup_detail():
    return await quart.render_template('signup.jinja',page='signup',
                                       **app.util.getPageInfo())

@bp.route('/logout')
async def logout():
    token = quart.request.cookies.get('token')
    try:
        token_bytes = bytes.fromhex(token) # type:ignore
        app.database.deleteSession(token_bytes)
    except:
        pass
    ret = quart.Response(
        await quart.render_template('logout.jinja',page='logout',
                                    **app.util.getPageInfo()))
    ret.delete_cookie('token')
    return ret
