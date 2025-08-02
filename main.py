import quart
import sys

from app.database.connectionPool import closeDatabaseConnections
from app.database.logging import closeLogging

from app.pages.account import bp as bpAccount
from app.pages.api import bp as bpApi
from app.pages.error import bp as bpError
from app.pages.factor import bp as bpFactor
from app.pages.number import bp as bpNumber
from app.pages.root import bp as bpRoot
from app.pages.tables import bp as bpTables

from app.config import MAX_CONTENT_LENGTH, PROXY_FIX_MODE, PROXY_FIX_HOPS

# note that "app" is both the package name and the variable name
# this has not caused any problems yet

app = quart.Quart(__name__)
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

app.register_blueprint(bpAccount)
app.register_blueprint(bpApi)
app.register_blueprint(bpError)
app.register_blueprint(bpFactor)
app.register_blueprint(bpNumber)
app.register_blueprint(bpRoot)
app.register_blueprint(bpTables)

@app.after_serving
async def dbcon_close():
    sys.stderr.write('closing database stuff\n')
    closeDatabaseConnections()
    closeLogging()

# for development
if __name__ == '__main__':
    app.run(port=65519,debug=True)
    '''
    for production run with: `hypercorn -b addr:port main:app`
    possible options:
    --access-logfile <file for access log>
    --log-level <default is info>
    --workers <number of workers>
    note: jinja cache defaults to 50 templates
    '''

# for production, apply proxy fix middleware if needed
elif PROXY_FIX_MODE is not None:
    from hypercorn.middleware import ProxyFixMiddleware
    assert PROXY_FIX_MODE in ('legacy','modern')
    app = ProxyFixMiddleware(app,
                             mode=PROXY_FIX_MODE,
                             trusted_hops=PROXY_FIX_HOPS)
