import quart

async def basicErrorPage(msg:str,code:int):
    page = None
    match code:
        case 400:
            page = await quart.render_template('error/400.jinja',msg=msg)
        case 401:
            page = await quart.render_template('error/401.jinja',msg=msg)
        case 403:
            page = await quart.render_template('error/403.jinja',msg=msg)
        case 404:
            page = await quart.render_template('error/404.jinja',msg=msg)
        case _:
            assert 0, f'unsupported error code for basic error page: {code}'
    return quart.Response(page,code)
