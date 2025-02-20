import quart

import app.util
import app.maths
import app.database
from app.config import MAX_FACTORS_LEN, MAX_DETAILS_LEN
from app.config import _ln2_d_ln10

bp = quart.Blueprint('factor',__name__)

def getFactorInfo(i:int):
    '''
    gets details for factor.jinja template
    '''
    row = app.database.getFactorByID(i)
    if row is None:
        return { 'exists': False, 'factor_id': i }

    ret = { 'exists': True, 'factor_id': i }
    f_str = str(row.value)

    ret['factor_value'] = f_str
    ret['factor_len'] = len(f_str)
    ret['factor_bits'] = row.value.bit_length()
    ret['primality'] = row.primality
    ret['factor1_exists'] = row.f1_id is not None
    ret['factor2_exists'] = row.f2_id is not None
    ret['factor1_id'] = row.f1_id
    ret['factor2_id'] = row.f2_id
    ret['factors_old'] = app.database.getOldFactors(i)

    if row.f1_id is not None and row.f2_id is not None:
        frow1 = app.database.getFactorByID(row.f1_id)
        frow2 = app.database.getFactorByID(row.f2_id)
        assert frow1 is not None and frow2 is not None, 'internal error'

        ret['factor1_value'] = frow1.value
        ret['factor2_value'] = frow2.value
        ret['factor1_status'] = frow1.primality
        ret['factor2_status'] = frow2.primality

    return ret

@bp.get('/factor/<int:i>')
async def factor_get(i:int):
    factor_info = getFactorInfo(i)
    code = 200 if factor_info['exists'] else 404
    return quart.Response(
        await quart.render_template('factor.jinja',page='factor',
                                    **app.util.getPageInfo(),
                                    **factor_info),code)

def updatePrimality(i:int,status:str,run_prp:str) -> tuple[str,int,bool]:
    '''
    process form for updating primality
    returns (msg,code,ok)
    '''
    if run_prp not in ('0','1'):
        return ('Invalid run PRP boolean.',400,False)
    run_prp_b = (run_prp == '1')

    if status == '0':
        try:
            app.database.setFactorComposite(i,run_prp_b)
            return ('Factor successfully set as composite.',200,True)
        except Exception as e:
            return (f'Failed to update status: {e}',400,False)

    elif status == '2':
        try:
            app.database.setFactorPrime(i,run_prp_b)
            return ('Factor successfully set as prime.',200,True)
        except Exception as e:
            return (f'Failed to update status: {e}',400,False)

    else:
        return ('Invalid primality status.',400,False)

def insertFactors(i:int,u:None|app.database.UserRow,name:str,
                  factors:str,details:str) -> tuple[str,int,bool]:
    '''
    process form for inserting factors
    returns (msg,code,ok)
    '''
    row = app.database.getFactorByID(i)
    if row is None:
        return ('Invalid factor ID.',404,False)

    if len(factors) > MAX_FACTORS_LEN or len(details) > MAX_DETAILS_LEN \
            or len(name) > 64:
        return ('Submission length limit exceeded.',400,False)

    # identify numbers in the submission
    cof = row.value
    nums = set()
    cof_len = 1 + int(cof.bit_length() * _ln2_d_ln10)
    for word in factors.split():
        if len(word) <= cof_len:
            try:
                n = int(word)
                if 1 < n < cof:
                    nums.add(n)
            except:
                pass

    # search for factors in smallest to largest order
    count_found = 0
    for f in sorted(nums):
        if f >= cof:
            break
        if cof % f != 0:
            continue
        try:
            app.database.addFactor(cof,f)
            cof //= f
            count_found += 1
        # only catch FDBException to allow internal asserts to be obvious
        except app.database.FDBException:
            pass

    user_id = None if u is None else u.id
    ip = quart.request.remote_addr

    if count_found > 0:
        app.database.insertFactorForm(user_id,name,factors,details,ip,i)
        return ('Factorization successful.',200,True)
    else:
        return ('Did not find any new factors.',400,False)

@bp.post('/factor/<int:i>')
async def factor_post(i:int):
    data = await quart.request.form
    user = app.util.getUser()
    code = 200
    ok = False

    if 'primality' in data and 'run_prp' in data:

        if user is None:
            return await app.util.blank401(f'/factor/{i}')

        if not user.is_admin:
            return await app.util.blank403(f'/factor/{i}')

        msg,code,ok = updatePrimality(i,data['primality'],data['run_prp'])

    elif 'factors' in data and 'details' in data and 'name' in data:
        msg,code,ok = insertFactors(i,user,data['name'],
                                    data['factors'],data['details'])

    else:
        return await app.util.blank400(f'/factor/{i}')

    return quart.Response(
        await quart.render_template('factor.jinja',page='factor',
                                    post_ok=ok,post_msg=msg,
                                    **app.util.getPageInfo(),
                                    **getFactorInfo(i)),code)
