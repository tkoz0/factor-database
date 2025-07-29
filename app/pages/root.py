import quart

from app.utils.pageData import basePageData

bp = quart.Blueprint('root',__name__)

@bp.route('/')
async def root():
    return await quart.render_template('home.jinja',
                                       page='home',
                                       **basePageData())

@bp.route('/index')
async def rootIndex():
    return await root()

@bp.route('/about')
async def about():
    return await quart.render_template('about.jinja',
                                       page='about',
                                       **basePageData())

@bp.route('/guide')
async def guide():
    return await quart.render_template('guide.jinja',
                                       page='guide',
                                       **basePageData())

@bp.route('/privacy')
async def privacy():
    return await quart.render_template('privacy.jinja',
                                       page='privacy',
                                       **basePageData())

@bp.route('/stats')
async def stats():
    return await quart.render_template('stats.jinja',
                                       page='stats',
                                       **basePageData())

@bp.route('/recent')
async def recent():
    return await quart.render_template('recent.jinja',
                                       page='recent',
                                       **basePageData())

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
