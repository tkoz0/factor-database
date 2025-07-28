import quart

import app.util

bp = quart.Blueprint('root',__name__)

@bp.route('/')
async def root():
    return await quart.render_template('home.jinja',page='home',
                                       **app.util.getPageInfo())

@bp.route('/index')
async def root2():
    return await root()

@bp.route('/about')
async def about():
    return await quart.render_template('about.jinja',page='about',
                                       **app.util.getPageInfo())

@bp.route('/guide')
async def guide():
    return await quart.render_template('guide.jinja',page='guide',
                                       **app.util.getPageInfo())

@bp.route('/privacy')
async def privacy():
    return await quart.render_template('privacy.jinja',page='privacy',
                                       **app.util.getPageInfo())

@bp.route('/stats')
async def stats():
    return await quart.render_template('stats.jinja',page='stats',
                                       **app.util.getPageInfo())

@bp.route('/recent')
async def recent():
    return await quart.render_template('recent.jinja',page='recent',
                                       **app.util.getPageInfo())

@bp.route('/robots.txt')
async def robots():
    return await quart.send_file('static/robots.txt')

@bp.route('/favicon.ico')
async def favicon():
    return await quart.send_file('static/favicon.ico')

# url format contains
# /<path>[?<args>][#<id>]
# path is the filesystem like path to the page/resource
# args look like arg1=value1&arg2=value2
# id is for a specific part of the page
# args are accessible with quart.request.args
