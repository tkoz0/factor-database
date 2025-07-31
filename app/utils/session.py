import quart

import app.database.users as dbUsers

def getSession(token:str|None = None) -> dbUsers.SessionRow|None:
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
    return dbUsers.getSession(token_bytes)

def getUser(user:str|int|None = None) -> dbUsers.UserRow|None:
    '''
    returns the user based on the token cookie
    or from username/email/id id specified
    '''
    if user is None:
        session = getSession()
        if session is None:
            return None
        return dbUsers.getUser(session.user_id)
    return dbUsers.getUser(user)
