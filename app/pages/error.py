import quart

bp = quart.Blueprint('error',__name__)

@bp.route('/<path:path>')
async def error404(path):
    # any page not matching a programmed route should give 404
    return await quart.render_template('404.jinja',path=path),404

# codes
# 200 = ok
# 201 = created
# 202 = accepted
# 204 = no content
# 301 = moved
# 400 = bad request
# 401 = unauthorized (identity unknown)
# 403 = forbidden (identity known)
# 404 = not found
# 405 = method not allowed
# 410 = gone
# 414 = uri too long
# 418 = im a teapot (april fools joke)
# 429 = too many requests
