'''
manages categories and tables for listing number sequences
'''

import psycopg
import psycopg.sql
import re
from typing import Generator

from app.database.connectionPool import FdbConnection
from app.database.helpers import \
    stringToPath, \
    pathToString, \
    FdbException
from app.database.logging import logDatabaseInfoMessage
from app.database.numbers import \
    _getNumberByValue, \
    _getNumberById, \
    deleteNumberById, \
    NumberRow, \
    _getNumberFactorizationHelper

from app.config import DEBUG_EXTRA

# what a path component is allowed to contain
_PATH_NAME_RE = re.compile(r'[\w\+\-\=][\w\+\-\=\.]*')

'''
factor tables are organized into categories, like filesystem directories
the root category is a directory represented by the empty tuple ()
other categories/tables are represented by a tuple of strings (path components)
categories store categories or tables, tables display factorizations
a table stores a sequence of numbers starting at an index >= 0

categories have a title for display and html info
they can also store an expression for nth terms which is currently unused
'''

class CategoryRow:
    '''
    object representation for a row in the categories table
    (row in "select * from categories")
    TODO document table columns
    '''

    def __init__(self,row):
        if DEBUG_EXTRA:
            assert isinstance(row,tuple)
            assert len(row) == 8
            assert isinstance(row[0],int)
            assert isinstance(row[1],int)
            assert row[2] is None or isinstance(row[2],int)
            assert isinstance(row[3],str)
            assert isinstance(row[4],str)
            assert isinstance(row[5],bool)
            assert isinstance(row[6],str)
            assert row[7] is None or isinstance(row[7],str)
        self.id: int = row[0]
        self.parent_id: int = row[1]
        self.order_num: int|None = row[2]
        self.name: str = row[3]
        self.title: str = row[4]
        self.is_table: bool = row[5]
        self.info: str = row[6]
        self.expr: str|None = row[7]

    def __repr__(self) -> str:
        return f'<CategoryRow(' \
            f'id={self.id},' \
            f'parent_id={self.parent_id},' \
            f'order_num={self.order_num},' \
            f'name={repr(self.name)},' \
            f'title={repr(self.title)},' \
            f'is_table={self.is_table},' \
            f'info={repr(self.info)},' \
            f'expr={repr(self.expr)})>'

def _getCategoryById(i:int,con:psycopg.Connection,/) -> None|CategoryRow:
    # get category by id (from connection)
    cur = con.execute("select * from categories where id = %s;",(i,))
    row = cur.fetchone()
    return None if row is None else CategoryRow(row)

def _getCategoryByPath(path:tuple[str,...],con:psycopg.Connection,/) \
        -> None|list[CategoryRow]:
    # get categogry by path (from connection)
    row = _getCategoryById(0,con)
    assert row is not None, 'internal error (root category never created)'
    ret = [row]

    for p in path:
        cur = con.execute("select * from categories "
                          "where parent_id = %s and name = %s;",
                          (row.id,p))
        row2 = cur.fetchone()
        if row2 is None:
            return None

        if DEBUG_EXTRA:
            assert cur.fetchone() is None, 'internal error (duplicate path)'

        row = CategoryRow(row2)
        ret.append(row)

    return ret

def _getCategoryPathById(i:int,con:psycopg.Connection,/) \
        -> None|list[CategoryRow]:
    # full category path details from id (going back up to root)
    row = _getCategoryById(i,con)
    if row is None:
        return None

    ret = [row]
    while row.id != 0:
        cur = con.execute("select * from categories where id = %s;",
                          (row.parent_id,))
        row2 = cur.fetchone()
        assert row2 is not None, 'internal error (parent does not exist)'

        if DEBUG_EXTRA:
            assert cur.fetchone() is None, 'internal error (duplicate id)'

        row = CategoryRow(row2)
        ret.append(row)

    # switch order to start at root
    return ret[::-1]

def getCategory(pathOrId:int|tuple[str,...]|str,/) -> None|CategoryRow:
    '''
    find category info by its path/id, empty tuple or 0 is root,
    none if it does not exist
    '''
    if isinstance(pathOrId,str):
        pathOrId = stringToPath(pathOrId)

    with FdbConnection() as con:
        if isinstance(pathOrId,tuple):
            data = _getCategoryByPath(pathOrId,con)
            return None if data is None else data[-1]
        else:
            return _getCategoryById(pathOrId,con)

def getCategoryFullPath(pathOrId:int|tuple[str,...]|str,/) \
        -> None|list[CategoryRow]:
    '''
    find info of a category and all its parents, empty path is root
    none if it does not exist
    '''
    if isinstance(pathOrId,str):
        pathOrId = stringToPath(pathOrId)

    with FdbConnection() as con:
        if isinstance(pathOrId,tuple):
            return _getCategoryByPath(pathOrId,con)
        else:
            return _getCategoryPathById(pathOrId,con)

def _getCategoryParentById(i:int,con:psycopg.Connection,/) -> None|CategoryRow:
    # get category parent
    cur = con.execute("select parent_id from categories where id = %s;",(i,))
    row = cur.fetchone()
    if row is None:
        return None
    return _getCategoryById(row[0],con)

def getCategoryParent(pathOrId:int|tuple[str,...]|str,/) -> None|CategoryRow:
    '''
    find parent of category, parent of root is none,
    non if it does not exist
    '''
    if isinstance(pathOrId,str):
        pathOrId = stringToPath(pathOrId)

    with FdbConnection() as con:
        if isinstance(pathOrId,tuple):
            if pathOrId == ():
                return None
            data = _getCategoryByPath(pathOrId[:-1],con)
            return None if data is None else data[-1]
        else:
            return _getCategoryParentById(pathOrId,con)

def _getCategoryChildrenById(i:int,con:psycopg.Connection,/) \
        -> list[CategoryRow]:
    # get category children (excluding root as a child of root)
    cur = con.execute("select * from categories where parent_id = %s "
                      "and id <> 0 order by order_num nulls last;",(i,))
    return [CategoryRow(row) for row in cur]

def listCategory(pathOrId:int|tuple[str,...]|str,/) -> None|list[CategoryRow]:
    '''
    list category children (by id)
    empty list if it does not exist
    empty list is still possible for categories that do exist
    '''
    if isinstance(pathOrId,str):
        pathOrId = stringToPath(pathOrId)

    with FdbConnection() as con:
        if isinstance(pathOrId,tuple):
            data = _getCategoryByPath(pathOrId,con)
            if data is None:
                return None
            return _getCategoryChildrenById(data[-1].id,con)
        else:
            return _getCategoryChildrenById(pathOrId,con)

def createCategory(path:tuple[str,...]|str,/,is_table:bool,
                   title:str,info:str) -> CategoryRow:
    '''
    creates a subcategory (cannot be root), its parent must exist
    exception if an error occurs
    returns row of new category
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    if path == ():
        raise FdbException('root category must be created in database setup')

    if not _PATH_NAME_RE.fullmatch(path[-1]):
        raise FdbException(f'invalid path name: {repr(path[-1])}')

    with FdbConnection() as con:

        # make sure parent category exists
        parent = _getCategoryByPath(path[:-1],con)
        if parent is None:
            raise FdbException('parent does not exist')
        parent = parent[-1]

        # create subcategory
        cur = con.execute("insert into categories "
                          "(parent_id,name,title,is_table,info) "
                          "values (%s,%s,%s,%s,%s) returning *;",
                          (parent.id,path[-1],title,is_table,info))

        new_row = CategoryRow(cur.fetchone())
        logDatabaseInfoMessage(
            f'created {'table' if is_table else 'category'} '
            f'id {new_row.id} with path {pathToString(path)}')
        con.commit()
        return new_row

# prepare queries for the columns that may be updated in categories table
_SET_CATEGORY_COLUMN_QUERIES = dict()
_GET_CATEGORY_COLUMN_QUERIES = dict()
for column in ('title','info','expr'):
    query = psycopg.sql.SQL("update categories set {} = %s where id = %s;")
    query = query.format(psycopg.sql.Identifier(column))
    _SET_CATEGORY_COLUMN_QUERIES[column] = query
    query = psycopg.sql.SQL("select {} from categories where id = %s;")
    query = query.format(psycopg.sql.Identifier(column))
    _GET_CATEGORY_COLUMN_QUERIES[column] = query

def _setCategoryColumn(pathOrId:int|tuple[str,...]|str,value,column:str,/):
    if isinstance(pathOrId,str):
        pathOrId = stringToPath(pathOrId)

    with FdbConnection() as con:
        if isinstance(pathOrId,tuple):
            pathdata = _getCategoryByPath(pathOrId,con)
            if pathdata is not None:
                pathdata = pathdata[-1]
        else:
            pathdata = _getCategoryById(pathOrId,con)

        if pathdata is None:
            raise FdbException('category does not exist')

        con.execute(_SET_CATEGORY_COLUMN_QUERIES[column],(value,pathdata.id))
        con.commit()

        if isinstance(pathOrId,tuple):
            logDatabaseInfoMessage(
                f'updated {column} for {pathToString(pathOrId)}')
        else:
            logDatabaseInfoMessage(
                f'updated {column} for category id {pathOrId}')

def _getCategoryColumn(pathOrId:int|tuple[str,...]|str,column:str,/):
    if isinstance(pathOrId,str):
        pathOrId = stringToPath(pathOrId)

    with FdbConnection() as con:
        if isinstance(pathOrId,tuple):
            pathdata = _getCategoryByPath(pathOrId,con)
            if pathdata is not None:
                pathdata = pathdata[-1]
        else:
            pathdata = _getCategoryById(pathOrId,con)

        if pathdata is None:
            raise FdbException('category does not exist')

        con.execute(_GET_CATEGORY_COLUMN_QUERIES[column],(pathdata.id,))

        if isinstance(pathOrId,tuple):
            return pathOrId[0]
        else:
            return None

def setCategoryInfo(pathOrId:int|tuple[str,...]|str,/,info:str):
    '''
    update the category info string
    '''
    _setCategoryColumn(pathOrId,info,'info')

def setCategoryTitle(pathOrId:int|tuple[str,...]|str,/,title:str):
    '''
    update the category title string
    '''
    _setCategoryColumn(pathOrId,title,'title')

def setCategoryExpr(pathOrId:int|tuple[str,...]|str,/,expr:str|None):
    '''
    update the category expression for generating terms
    '''
    _setCategoryColumn(pathOrId,expr,'expr')

def getCategoryInfo(pathOrId:int|tuple[str,...]|str,/) -> str|None:
    '''
    get category info string
    '''
    _getCategoryColumn(pathOrId,'info')

def getCategoryTitle(pathOrId:int|tuple[str,...]|str,/) -> str|None:
    '''
    get category title string
    '''
    _getCategoryColumn(pathOrId,'title')

def getCategoryExpr(pathOrId:int|tuple[str,...]|str,/) -> str|None:
    '''
    get category expression for generating terms
    '''
    _getCategoryColumn(pathOrId,'expr')

def renameCategory(old:tuple[str,...]|str,new:tuple[str,...]|str,/):
    '''
    moves/renames a category
    '''
    if isinstance(old,str):
        old = stringToPath(old)
    if isinstance(new,str):
        new = stringToPath(new)

    if old == () or new == ():
        raise FdbException('cannot rename root category')

    if not _PATH_NAME_RE.fullmatch(new[-1]):
        raise FdbException('invalid path name')

    with FdbConnection() as con:
        olddata = _getCategoryByPath(old,con)
        if olddata is None:
            raise FdbException('old path does not exist')
        newdata = _getCategoryByPath(new[:-1],con)
        if newdata is None:
            raise FdbException('new path parent does not exist')

        con.execute("update categories set parent_id = %s, order_num = null, "
                    "name = %s where id = %s;",
                    (newdata[-1].id,new[-1],olddata[-1].id))
        con.commit()
        logDatabaseInfoMessage(
            f'renamed {pathToString(old)} to {pathToString(new)}')

def deleteCategory(path:tuple[str,...]|str,/):
    '''
    delete a category from the database
    exception if it does not exist or has children
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    if path == ():
        raise FdbException('cannot remove root category')

    with FdbConnection() as con:
        data = _getCategoryByPath(path,con)
        if data is None:
            raise FdbException('path does not exist')

        con.execute('delete from categories where id = %s;',(data[-1].id,))
        con.commit()
        logDatabaseInfoMessage(f'deleted {pathToString(path)}')

def reorderSubcategories(path:tuple[str,...]|str,/,order:list[str]):
    '''
    changes listing order for subcategories
    exception if invalid order data or error occurs
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        data = _getCategoryByPath(path,con)
        if data is None:
            raise FdbException('path does not exist')

        children = _getCategoryChildrenById(data[-1].id,con)
        if len(children) != len(order):
            raise FdbException('list size != number of children')
        if set(order) != set(child.name for child in children):
            raise FdbException('list does not match child categories')
        ordermap = {name:i for i,name in enumerate(order)}

        queryparams = [(ordermap[child.name],child.id) for child in children]
        con.cursor().executemany("update categories set order_num = %s "
                                 "where id = %s;",queryparams)
        con.commit()
        logDatabaseInfoMessage(f'reordered listing for {pathToString(path)}')

def _walkCategories(row:CategoryRow,path:tuple[str,...],
                    con:psycopg.Connection,/) \
        -> Generator[tuple[tuple[str,...],CategoryRow],None,None]:
    # recursively find children
    yield (path,row)
    children = _getCategoryChildrenById(row.id,con)
    for child in children:
        yield from _walkCategories(child,path+(child.name,),con)

def walkCategories(path:tuple[str,...]|str=(),/) \
        -> Generator[tuple[tuple[str,...],CategoryRow],None,None]:
    '''
    iterate a categories subtree, default starting at root
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        data = _getCategoryByPath(path,con)
        if data is None:
            raise FdbException('path does not exist')
        yield from _walkCategories(data[-1],path,con)

def createCategoryNumber(path:tuple[str,...]|str,index:int,/,
                         value:int|str,expr:str):
    '''
    add a number to a category (must exist in database for integers >= 2)
    fs is the factor list passed to addNumber()
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        cat = _getCategoryByPath(path,con)
        if cat is None:
            raise FdbException('category does not exist')
        cat = cat[-1]
        if not cat.is_table:
            raise FdbException('numbers cat only be added to tables')

        # store string for numbers that cannot be in numbers table
        if isinstance(value,str) or value < 2:
            nid = None
            valstr = str(value)

        # make sure number exists and reference row
        else:
            num = _getNumberByValue(value,con)
            if num is None:
                raise FdbException('number does not exist')
            nid = num.id
            valstr = None

        con.execute("insert into sequences (cat_id,index,num_id,value,expr) "
                    "values (%s,%s,%s,%s,%s);",
                    (cat.id,index,nid,valstr,expr))
        con.commit()
        logDatabaseInfoMessage(f'created {pathToString(path)} index {index}')

def updateCategoryNumber(path:tuple[str,...]|str,index:int,/,expr:str|None):
    '''
    updates the expression stored for a number
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        cat = _getCategoryByPath(path,con)
        if cat is None:
            raise FdbException('category does not exist')
        cat = cat[-1]
        if not cat.is_table:
            raise FdbException('category numbers are only in tables')

        cur = con.execute("update sequences set expr = %s "
                          "where cat_id = %s and index = %s returning *;",
                          (expr,cat.id,index))
        updated = cur.fetchone() is not None
        con.commit()
        if updated:
            logDatabaseInfoMessage(
                f'updated {pathToString(path)} index {index}')

def deleteCategoryNumber(path:tuple[str,...]|str,index:int,/):
    '''
    remove a number from a category
    also attempts to remove it from the database
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        cat = _getCategoryByPath(path,con)
        if cat is None:
            raise FdbException('category does not exist')
        cat = cat[-1]

        cur = con.execute("delete from sequences where cat_id = %s and "
                          "index = %s returning num_id;",(cat.id,index))
        row = cur.fetchone()
        con.commit()
        if row is not None:
            logDatabaseInfoMessage(
                f'deleted {pathToString(path)} index {index}')
            deleteNumberById(row[0])

def getCategoryNumberRows(path:tuple[str,...]|str,/,start:int,count:int=1) \
        -> list[NumberRow]:
    '''
    gets row data for numbers in a category
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        cat = _getCategoryByPath(path,con)
        if cat is None:
            raise FdbException('category does not exist')
        cat = cat[-1]
        ret: list[NumberRow] = []

        cur = con.execute("select numbers.* from sequences join numbers "
                          "on sequences.num_id = numbers.id "
                          "where cat_id = %s and %s <= sequences.index and "
                          "sequences.index < %s order by sequences.index;",
                          (cat.id,start,start+count))
        for row in cur.fetchall():
            ret.append(NumberRow(row))

    return ret

def getCategoryNumberInfo(path:tuple[str,...]|str,/,start:int,count:int=1) \
        -> list[tuple[int,str,str|NumberRow,list[tuple[int,int,None|int]]]]:
    '''
    gets number table information for a category
    each is (index,expr,int|number_row,list[factor,primality,id])
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        cat = _getCategoryByPath(path,con)
        if cat is None:
            raise FdbException('category does not exist')
        cat = cat[-1]
        ret: list[tuple[int,str,str|NumberRow,list[tuple[int,int,None|int]]]] \
            = []

        cur = con.execute("select * from sequences where cat_id = %s "
                          "and %s <= index and index < %s "
                          "order by index;",(cat.id,start,start+count))
        for cat_id,index,num_id,value,expr in cur.fetchall():

            if DEBUG_EXTRA:
                assert cat_id == cat.id
                assert isinstance(index,int)
                assert num_id is None or isinstance(num_id,int)
                assert value is None or isinstance(value,str)
                assert expr is None or isinstance(expr,str)

            if expr is None:
                expr = ''

            if num_id is None: # number not stored in database
                ret.append((index,expr,value,[]))

            else: # number stored in database
                num = _getNumberById(num_id,con)
                assert num is not None, 'internal error'
                factors = _getNumberFactorizationHelper(num,con)
                assert factors is not None, 'internal error'
                ret.append((index,expr,num,factors))

        return ret

def findCategoriesWithNumber(i:int,/) \
        -> list[tuple[CategoryRow,int,tuple[str,...]]]:
    '''
    list of (row,index,path) for categories containing number id i
    '''
    with FdbConnection() as con:
        cur = con.execute("select cat_id,index from sequences "
                          "where num_id = %s;",(i,))
        cat_ids: list[tuple[int,int]] = cur.fetchall()
        ret: list[tuple[CategoryRow,int,tuple[str,...]]] = []

        for cat_id,index in cat_ids:
            row = _getCategoryById(cat_id,con)
            path = _getCategoryPathById(cat_id,con)
            assert row is not None, 'internal error'
            assert path is not None, 'internal error'
            ret.append((row,index,tuple(r.name for r in path[1:])))

        return ret

def findCategoryIndexRange(path:tuple[str,...]|str|int,/) \
        -> None|tuple[int,int]:
    '''
    find the min and max of the indexes in a category
    '''
    if isinstance(path,str):
        path = stringToPath(path)

    with FdbConnection() as con:
        if isinstance(path,tuple):
            row = _getCategoryByPath(path,con)
            if row is None:
                return None
            path = row[-1].id

        cur = con.execute("select min(index),max(index) from sequences "
                          "where cat_id = %s;",(path,))
        row = cur.fetchone()
        if row is not None:
            cmin,cmax = row
            if isinstance(cmin,int) and isinstance(cmax,int):
                return (cmin,cmax)
            else:
                return None
