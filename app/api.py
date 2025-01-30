import json

import quart

import app.util

bp = quart.Blueprint('api',__name__)

@bp.route('/api')
async def api():
    return await quart.render_template('api.jinja',page='api',
                                       **app.util.getPageInfo())
