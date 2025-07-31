import json
import quart

from app.utils.pageData import basePageData

bp = quart.Blueprint('api',__name__)

def toJson(obj,/) -> str:
    return json.dumps(obj,separators=(',',':'))

#def fromJson(s:str,/):
#    return json.loads(s)

def jsonResponse(obj,code=200,/) -> quart.Response:
    return quart.Response(toJson(obj),code,mimetype='application/json')

@bp.get('/api')
async def apiGet():
    '''
    api documentation
    '''
    return await quart.render_template('api.jinja',
                                       page='api',
                                       **basePageData())

@bp.post('/api')
async def apiPost():
    '''
    api usage
    '''
    return jsonResponse({'message':'not implemented'},501)
