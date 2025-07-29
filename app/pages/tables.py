import quart

import app.database
from app.utils.session import getUser
from app.utils.errorPage import basicErrorPage
from app.utils.factorData import factorsHtml
from app.utils.pageData import basePageData
from app.config import \
    DEBUG_EXTRA, \
    TABLE_PER_PAGE_DEFAULT, \
    TABLE_PER_PAGE_LIMIT

bp = quart.Blueprint('tables',__name__)

def tableInfo(path_str:str):
    '''
    generate table information for tables.jinja template
    '''
    # get index range args
    args = quart.request.args
    try:
        start = int(args.get('start')) # type:ignore
    except:
        start = 0
    try:
        count = int(args.get('count')) # type:ignore
    except:
        count = TABLE_PER_PAGE_DEFAULT

    # apply some reasonable bounds
    count = min(max(count,1),TABLE_PER_PAGE_LIMIT)
    start = min(max(start,0),1000000-count)

    path = () if path_str == '' else tuple(path_str.split('/'))
    path_str = '/'.join(path)
    cat_rows = app.database.getCategoryFullPath(path)

    if cat_rows is None:
        return {
            'path': path_str,
            'exists': False,
            'is_root': False
        }

    ret = {
        'path': path_str,
        'exists': True,
        'cat_rows': cat_rows,
        'count': count,
        'start': start,
        'max_count': TABLE_PER_PAGE_LIMIT
    }

    if DEBUG_EXTRA:
        assert len(path) + 1 == len(cat_rows)
        assert all(cat_rows[i+1].name == path[i] for i in range(len(path)))

    if path == (): # root
        ret['is_root'] = True
        ret['current_path'] = '/tables'
        ret['nav_data'] = None

    else: # not root
        ret['is_root'] = False

        link_paths = []
        link_titles = []
        link_names = []

        for cat_row in cat_rows:
            link_paths.append('/tables' if link_paths == []
                              else f'{link_paths[-1]}/{cat_row.name}')
            link_titles.append(cat_row.name if cat_row.title == ''
                               else cat_row.title)
            link_names.append(cat_row.name)

        ret['current_path'] = link_paths[-1]
        ret['nav_data'] = zip(link_names[1:],link_paths[1:])

    cat_row = cat_rows[-1]
    ret['is_table'] = cat_row.is_table
    ret['title'] = cat_row.name if cat_row.title == '' else cat_row.title
    ret['info'] = cat_row.info

    if cat_row.is_table:
        tabledata = app.database.getCategoryNumberInfo(path,start,count)
        ret['table'] = [
            (
                index,
                expr,
                row_or_value if isinstance(row_or_value,str)
                    else factorsHtml(factors),
                None if isinstance(row_or_value,str) else row_or_value.id,
                True if isinstance(row_or_value,str) else row_or_value.complete
            )
            for index,expr,row_or_value,factors in tabledata
        ]
        ret['index_range'] = app.database.findCategoryIndexRange(cat_row.id)

    else:
        child_rows = app.database.listCategory(cat_row.id)
        assert child_rows is not None, 'internal error'

        child_titles = []
        child_links = []
        child_is_table = []
        child_index_ranges = []

        for child_row in child_rows:
            child_titles.append(child_row.name if child_row.title == ''
                                else child_row.title)
            if path == ():
                child_links.append(f'/tables/{child_row.name}')
            else:
                child_links.append(f'/tables/{path_str}/{child_row.name}')
            child_is_table.append(child_row.is_table)
            child_index_ranges.append(
                app.database.findCategoryIndexRange(child_row.id))

        ret['children'] = zip(child_titles,child_links,
                              child_is_table,child_index_ranges)
        ret['children_len'] = len(child_rows)
        children_names = [cr.name for cr in child_rows]
        ret['children_names'] = children_names
        ret['reorder_list_initial'] = '\n'.join(children_names)+'\n'
        ret['reorder_list_size'] = len(children_names)

    return ret

#=============
# get requests
#=============

@bp.get('/tables')
async def tablesGetRoot():
    return await tablesGet('')

@bp.get('/tables/')
async def tablesGetRootWithSlash():
    return await tablesGet('')

@bp.get('/tables/<path:path>')
async def tablesGet(path:str):
    return await quart.render_template('tables.jinja',
                                       page='tables',
                                       **basePageData(),
                                       **tableInfo(path))

#==============
# post requests
#==============

@bp.post('/tables')
async def tablesPostRoot():
    return await tablesPost('')

@bp.post('/tables/')
async def tablesPostRootWithSlash():
    return await tablesPost('')

def reorderSubcategories(p:tuple[str,...],data:str) -> tuple[str,int,bool]:
    '''
    process form for reordering subcategories
    returns (msg,code,ok)
    '''
    if data == '':
        return ('List order not changed.',200,True)
    try:
        app.database.reorderSubcategories(p,data.splitlines())
        return ('Successfully reordered subcategories.',200,True)
    except Exception as e:
        return (f'Failed to reorder: {e}',400,False)

def updateDetails(p:tuple[str,...],title:str,info:str,preview:bool) \
        -> tuple[str,int,bool,dict]:
    '''
    process form for editing title/info
    returns (msg,code,ok)
    '''
    if preview:
        return (f'Previewing changes',200,True,{
            'preview': True,
            'preview_title': title,
            'preview_info': info
        })
    else:
        try:
            app.database.setCategoryTitle(p,title)
            app.database.setCategoryInfo(p,info)
            return ('Successfully updated information.',200,True,{})
        except Exception as e:
            return (f'Failed to update: {e}',400,False,{})

def createSubcategory(p:tuple[str,...],newname:str,cattype:str,newtitle:str) \
        -> tuple[str,int,bool]:
    '''
    process form for creating a subcategory or table
    returns (msg,code,ok)
    '''
    if cattype not in ('cat','tab'):
        return ('Invalid category type.',400,False)
    is_table = cattype == 'tab'
    try:
        app.database.createCategory(p+(newname,),is_table,newtitle,'')
        return (f'Successfully created '
                f'{'table' if is_table else 'subcategory'}',
                200,True)
    except Exception as e:
        return (f'Failed to create: {e}',400,False)

def renameCategory(p:tuple[str,...],newpath:str) -> tuple[str,int,bool]:
    '''
    process form for renaming category/table
    '''
    try:
        np_tup = tuple(newpath.split('/'))
        app.database.renameCategory(p,np_tup)
        return (f'Renamed successfully. Go to it at <a '
                f'href="/tables/{newpath}">here</a>.',
                200,True)
    except Exception as e:
        return (f'Failed to rename: {e}',400,False)

def deleteCategory(p:tuple[str,...],confirm:str) -> tuple[str,int,bool]:
    '''
    process form for deleting category/table
    '''
    if p == ():
        return ('Cannot delete root.',400,False)
    if p[-1] != confirm:
        return ('Confirmation failed.',400,False)
    try:
        app.database.deleteCategory(p)
        return (f'Deleted successfully. Go to its parent <a '
                f'href="/tables/{'/'.join(p[:-1])}">here</a>.',
                200,True)
    except Exception as e:
        return (f'Failed to delete: {e}',400,False)

def insertNumbers(p:tuple[str,...],indexes:list[str],exprs:list[str],
                  values:list[str]) -> tuple[str,int,bool]:
    '''
    process form for adding numbers to table
    '''
    try:
        assert len(indexes) == len(exprs) == len(values), 'mismatched lengths'
        arg_i = [int(i) for i in indexes]
        arg_v = [int(v) for v in values]
        for i in range(len(exprs)):
            app.database.createCategoryNumber(p,arg_i[i],arg_v[i],exprs[i])
        return (f'Successfully created {len(exprs)} number(s).',200,True)
    except Exception as e:
        return (f'Failed to create: {e}',400,False)

def removeNumbers(p:tuple[str,...],indexes:str,confirm:str) \
        -> tuple[str,int,bool]:
    '''
    process form for removing numbers from table
    '''
    if p == ():
        return ('Root should not be a table.',400,False)
    if p[-1] != confirm:
        return ('Confirmation failed.',400,False)
    try:
        ilist = indexes.split()
        for i in map(int,ilist):
            app.database.deleteCategoryNumber(p,i)
        return (f'Successfully deleted {len(ilist)} numbers.',200,True)
    except Exception as e:
        return (f'Failed to delete: {e}',400,False)

@bp.post('/tables/<path:path>')
async def tablesPost(path:str):
    data = await quart.request.form
    user = getUser()
    code = 200
    ok = False
    path_tup = () if path == '' else tuple(path.split('/'))

    if user is None:
        return await basicErrorPage(f'/tables/{path}',401)

    if not user.is_admin:
        return await basicErrorPage(f'/tables/{path}',403)

    # stores extra args that may be used for jinja template
    page_args = dict()

    # logged in as admin so actions are safe to perform from here
    table_info = tableInfo(path)
    if table_info['exists']:
        cat_rows = table_info['cat_rows']
        assert isinstance(cat_rows,list), 'internal error'
    else:
        return quart.Response(
            await quart.render_template('404.jinja',path=f'/tables/{path}'),404)

    if 'reorder_list' in data:
        msg,code,ok = reorderSubcategories(path_tup,data['reorder_list'])

    elif 'title' in data and 'info' in data:
        msg,code,ok,page_args = updateDetails(path_tup,
                                              data['title'],
                                              data['info'],
                                              'preview' in data)

    elif 'newcat_title' in data and 'newcat_name' in data \
            and 'subcat_type' in data:
        msg,code,ok = createSubcategory(path_tup,data['newcat_name'],
                                        data['subcat_type'],
                                        data['newcat_title'])

    elif 'new_path' in data:
        msg,code,ok = renameCategory(path_tup,data['new_path'])

    elif 'delete_confirm_1' in data:
        msg,code,ok = deleteCategory(path_tup,data['delete_confirm_1'])

    elif 'index0' in data and 'expr0' in data and 'value0' in data:
        i = 0
        indexes = []
        exprs = []
        values = []
        while f'index{i}' in data and f'expr{i}' in data \
                and f'value{i}' in data:
            indexes.append(data[f'index{i}'])
            exprs.append(data[f'expr{i}'])
            values.append(data[f'value{i}'])
            i += 1
        msg,code,ok = insertNumbers(path_tup,indexes,exprs,values)

    elif 'delete_index_list' in data and 'delete_confirm_2' in data:
        msg,code,ok = removeNumbers(path_tup,data['delete_index_list'],
                                    data['delete_confirm_2'])

    else:
        return await basicErrorPage(f'/tables/{path}',400)

    return quart.Response(
        await quart.render_template('tables.jinja',page='tables',
                                    post_ok=ok,post_msg=msg,
                                    **basePageData(),
                                    **tableInfo(path),**page_args),
                                    code)
