import quart

import app.database as db

def getSession(token:str|None = None) -> db.SessionRow|None:
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
    return db.getSession(token_bytes)

def getUser(user:str|int|None = None) -> db.UserRow|None:
    '''
    returns the user based on the token cookie
    or from username/email/id id specified
    '''
    if user is None:
        session = getSession()
        if session is None:
            return None
        return db.getUser(session.user_id)
    return db.getUser(user)
