import quart

from app.config import ADMIN_EMAIL,DEBUG_EXTRA
import app.utils.session as fdbSession

# TODO pages that have not been implemented yet
# removed from header: ('recent','/recent') and ('stats','/stats')
# removed from footer: ('guide','/guide') and ('api','/api')

# links to show when logged in (text,link)
_pages_header_user = [('home','/'),
                      ('tables','/tables'),
                      ('account','/account')]

_pages_footer_user = [('about','/about'),
                      ('privacy','/privacy')]

# links to show when anonymous (text,link)
_pages_header_anon = [('home','/'),
                      ('tables','/tables'),
                      ('login','/login'),
                      ('signup','/signup')]

_pages_footer_anon = [('about','/about'),
                      ('privacy','/privacy')]

def basePageData(token:str|None = None):
    '''
    returns base details used to render page templates
    - login information
    - links to show on header/footer
    token may be provided, otherwise it comes from cookie
    '''
    session = fdbSession.getSession(token)

    if session is None: # not logged in
        return {
            'remote_addr': quart.request.remote_addr,
            'logged_in': False,
            'headlinks': _pages_header_anon,
            'footlinks': _pages_footer_anon,
            'admin_email': ADMIN_EMAIL,
            'debug': DEBUG_EXTRA
        }

    else: # logged in
        user = fdbSession.getUser(session.user_id)
        assert user is not None, 'internal error'
        return {
            'remote_addr': quart.request.remote_addr,
            'logged_in': True,
            'username': user.username,
            'email': user.email,
            'fullname': user.username if user.fullname == '' else user.fullname,
            'is_admin': user.is_admin,
            'is_disabled': user.is_disabled,
            'headlinks': _pages_header_user,
            'footlinks': _pages_footer_user,
            'admin_email': ADMIN_EMAIL,
            'debug': DEBUG_EXTRA,
            'sess_exp': session.expires.replace(microsecond=0)
        }
