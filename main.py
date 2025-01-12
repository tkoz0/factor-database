import quart
import os
import sys

import app.database as db

sys.path.append(os.path.dirname(sys.argv[0]))

from app.account import bp as auth_blueprint
from app.api import bp as api_blueprint
from app.error import bp as error_blueprint
from app.factor import bp as factor_blueprint
from app.root import bp as root_blueprint
from app.tables import bp as tables_blueprint
from app.number import bp as number_blueprint
from app.config import MAX_CONTENT_LENGTH

app = quart.Quart(__name__)
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

app.register_blueprint(api_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(error_blueprint)
app.register_blueprint(factor_blueprint)
app.register_blueprint(root_blueprint)
app.register_blueprint(tables_blueprint)
app.register_blueprint(number_blueprint)

@app.after_serving
async def dbcon_close():
    sys.stderr.write('closing database stuff\n')
    db.closeDatabaseConnections()
    db.closeLogging()

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
