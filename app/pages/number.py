import quart

import app.util
import app.database
from app.database import Primality

bp = quart.Blueprint('numbers',__name__)

def getNumberInfo(i:int):
    '''
    gets details for number.jinja template
    '''
    row = app.database.getNumberByID(i)
    if row is None:
        return { 'exists': False, 'number_id': i }

    cof_row = None if row.cof_id is None \
        else app.database.getFactorByID(row.cof_id)
    number_value = str(row.value)
    factors_list = app.database.getNumberFactorizationByID(i)
    assert factors_list is not None, 'internal error'
    cats = app.database.findCategoriesWithNumber(i)
    cats_list = [
        (row.title if row.title else row.name,
        index,'/'.join(path))
        for row,index,path in cats
    ]
    factors_prog = app.util.factoringProgress(row.value,factors_list)

    return {
        'exists': True,
        'number_id': i,
        'number_len': len(number_value),
        'number_bits': row.value.bit_length(),
        'number_value': number_value,
        'number_complete': row.complete,
        'progress_str': f'{factors_prog*100:.2f}%',
        'small_factors': app.util.makeSmallFactorsHTML(row.spfs),
        'cofactor_id': row.cof_id,
        'cofactor_value': None if cof_row is None else cof_row.value,
        'cofactor_status': None if cof_row is None else
            'unknown' if cof_row.primality == Primality.UNKNOWN else
            'composite' if cof_row.primality == Primality.COMPOSITE else
            'probable prime' if cof_row.primality == Primality.PROBABLE else
            'proven prime' if cof_row.primality == Primality.PRIME else 'error',
        'factors_string': app.util.makeFactorsHTML(factors_list),
        'category_list': cats_list
    }

@bp.get('/number/<int:i>')
async def number_get(i:int):
    number_info = getNumberInfo(i)
    code = 200 if number_info['exists'] else 404
    return quart.Response(
        await quart.render_template('number.jinja',page='number',
                                    **app.util.getPageInfo(),
                                    **number_info),code)

def completeNumber(i:int) -> tuple[str,int,bool]:
    '''
    admin form for number completion
    '''
    try:
        if app.database.completeNumber(i):
            return ('Number factorization completed.',200,True)
        else:
            return ('Number optimized, incomplete.',200,True)
    except Exception as e:
        return (f'Failed to complete: {e}',400,False)

@bp.post('/number/<int:i>')
async def number_post(i:int):
    data = await quart.request.form
    user = app.util.getUser()
    code = 200
    ok = False

    if 'complete' in data and data['complete'] == '1':

        if user is None:
            return await app.util.blank401(f'/number/{i}')

        if not user.is_admin:
            return await app.util.blank403(f'/number/{i}')

        msg,code,ok = completeNumber(i)

    else:
        return await app.util.blank400(f'/number/{i}')

    return quart.Response(
        await quart.render_template('number.jinja',page='number',
                                    post_ok=ok,post_msg=msg,
                                    **app.util.getPageInfo(),
                                    **getNumberInfo(i)),code)
