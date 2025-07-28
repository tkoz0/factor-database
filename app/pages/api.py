import json
import quart

import app.util

bp = quart.Blueprint('api',__name__)

def toJson(obj,/) -> str:
    return json.dumps(obj,separators=(',',':'))

#def fromJson(s:str,/):
#    return json.loads(s)

def jsonResponse(obj,code=200,/) -> quart.Response:
    return quart.Response(toJson(obj),code,mimetype='application/json')

@bp.get('/api')
async def apiGet():
    return await quart.render_template('api.jinja',page='api',
                                       **app.util.getPageInfo())

@bp.post('/api')
async def apiPost():
    return jsonResponse({'message':'not implemented'},501)
