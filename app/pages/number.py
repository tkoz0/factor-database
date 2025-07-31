import quart

import app.database.numbers as dbNum
import app.database.categories as dbCat
from app.database.numbers import Primality

from app.utils.pageData import basePageData
from app.utils.factorData import \
    factoringProgress, \
    smallFactorsHtml, \
    factorsHtml
from app.utils.session import getUser
from app.utils.errorPage import basicErrorPage

bp = quart.Blueprint('numbers',__name__)

def numberInfo(i:int):
    '''
    gets details for number.jinja template
    '''
    row = dbNum.getNumberById(i)
    if row is None:
        return { 'exists': False, 'number_id': i }

    cof_row = None if row.cof_id is None \
        else dbNum.getFactorById(row.cof_id)
    number_value = str(row.value)
    factors_list = dbNum.getNumberFactorizationById(i)
    assert factors_list is not None, 'internal error'
    cats = dbCat.findCategoriesWithNumber(i)
    cats_list = [
        (row.title if row.title else row.name,
        index,'/'.join(path))
        for row,index,path in cats
    ]
    factors_prog = factoringProgress(row.value,factors_list)

    return {
        'exists': True,
        'number_id': i,
        'number_len': len(number_value),
        'number_bits': row.value.bit_length(),
        'number_value': number_value,
        'number_complete': row.complete,
        'progress_str': f'{factors_prog*100:.2f}%',
        'small_factors': smallFactorsHtml(row.spfs),
        'cofactor_id': row.cof_id,
        'cofactor_value': None if cof_row is None else cof_row.value,
        'cofactor_status': None if cof_row is None else
            'unknown' if cof_row.primality == Primality.UNKNOWN else
            'composite' if cof_row.primality == Primality.COMPOSITE else
            'probable prime' if cof_row.primality == Primality.PROBABLE else
            'proven prime' if cof_row.primality == Primality.PRIME else 'error',
        'factors_string': factorsHtml(factors_list),
        'category_list': cats_list
    }

@bp.get('/number/<int:i>')
async def numberGet(i:int):
    number_info = numberInfo(i)
    code = 200 if number_info['exists'] else 404
    return quart.Response(
        await quart.render_template('number.jinja',
                                    page='number',
                                    **basePageData(),
                                    **number_info),
        code)

def completeNumber(i:int) -> tuple[str,int,bool]:
    '''
    admin form for number completion
    '''
    try:
        if dbNum.completeNumber(i):
            return ('Number factorization completed.',200,True)
        else:
            return ('Number optimized, incomplete.',200,True)
    except Exception as e:
        return (f'Failed to complete: {e}',400,False)

@bp.post('/number/<int:i>')
async def numberPost(i:int):
    data = await quart.request.form
    user = getUser()
    code = 200
    ok = False

    if 'complete' in data and data['complete'] == '1':

        if user is None:
            return await basicErrorPage(f'/number/{i}',401)

        if not user.is_admin:
            return await basicErrorPage(f'/number/{i}',403)

        msg,code,ok = completeNumber(i)

    else:
        return await basicErrorPage(f'/number/{i}',400)

    return quart.Response(
        await quart.render_template('number.jinja',
                                    page='number',
                                    post_ok=ok,
                                    post_msg=msg,
                                    **basePageData(),
                                    **numberInfo(i)),
        code)
