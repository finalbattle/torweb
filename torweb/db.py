#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

def clone_table(table, name, metadata=None):
    from sqlalchemy import Table
    if not metadata:
        metadata = table.metadata
    try:
        return metadata.tables[name]
    except KeyError:
        args = []
        kwargs = {}
        args.append(name)
        args.append(metadata)
        for c in table.columns:
            args.append(c.copy())
        for c in table.constraints:
            args.append(c.copy())
        return Table(*args)


class QuerySet(object):
    def __init__(self, result):
        self.result = result

    def __getslice__(self, x, y):
        return self.result.limit(y-x).offset(x).execute().fetchall()

    def count(self):
        from sqlalchemy import func, select
        return select([func.count()]).select_from(self.result.alias()).execute().scalar()

    def __len__(self):
        return self.count()


class Result(object):
    def __init__(self, lst):
        self.lst = lst

    def get_one(self):
        if not self.lst:
            return None
        return self.lst[0]

    @staticmethod
    def set_variable(variable, value):
        variable.set(value, from_db=True)

    def __iter__(self):
        for row in self.lst:
            yield row

try:
    from storm.locals import create_database
    from storm.locals import Store
    from storm.store import ResultSet
    from storm import Undef
    from storm.exceptions import StormError, NotOneError
    class CacheResultSet(ResultSet):
        def fetchAll(self, cache, key, timeout=0):
            values_list = cache.get(key)
            if values_list is None:
                result = self._store._connection.execute(self._get_select())
                values_list = list(result)
                cache.set(key, values_list, timeout)
            else:
                result = Result(values_list)
            return [self._load_objects(result, values) for values in values_list]
        def fetchOne(self, cache, key, timeout=0):
            values = cache.get(key)
            if values is None:
                select = self._get_select()
                if select.limit is not Undef and select.limit > 2:
                    select.limit = 2
                result = self._store._connection.execute(select)
                values = result.get_one()
                if result.get_one():
                    raise NotOneError("one() used with more than one result available")
                cache.set(key, values, timeout)
            else:
                result = Result([values])
            if values:
                return self._load_objects(result, values)
            return None
    class CacheStore(Store):
        _result_set_factory = CacheResultSet
except ImportError:
    pass

try:
    from sqlalchemy.orm.query import Query
    class CacheQuery(Query):
        def fetchAll(self, cache, key, timeout=0):
            values_list = cache.get(key)
            if values_list is None:
                result_list = self.all()
                cache.set(key, result_list, timeout)
                return result_list
            return values_list
        def fetchOne(self, cache, key, timeout=0):
            value = cache.get(key)
            if value is None:
                value = self.one()
                cache.set(key, value, timeout)
                return value
            return value
        def fetchFirst(self, cache, key, timeout=0):
            value = get(key)
            if value is None:
                value = self.first()
                cache.set(key, value, timeout)
                return value
            return value
except ImportError:
    pass
