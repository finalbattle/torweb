#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import os
import yaml
from code import interact

class Yaml_Config(object):
    def __init__(self, base_path, yaml_path, url_root="/"):
        self.yaml_path = yaml_path
        f = open(self.yaml_path)
        self.settings = yaml.load(f)
        app_name = self.settings.get('app')
        self.app = __import__(app_name)
        self.app.base_path = base_path
        self.base_path = base_path
        self.init_store()
        self.init_propertys()
        self.set_url_root(url_root)
    def init_propertys(self):
        #self.app.base_path = self.base_path
        self.app.static_path = self.static_path
        self.app.static_url = self.static_url
        self.app.static_domain = self.static_domain
        self.app.cache = self.cache
        self.app.session_store = self.session_store
        self.app.settings = self
    #@property
    #def base_path(self):
    #    if not hasattr(self, '_base_path'):
    #        app_path = os.path.abspath(os.path.dirname(self.app.__file__))
    #        setattr(self, '_base_path', app_path)
    #    return getattr(self, '_base_path')
    @property
    def static_path(self):
        if not hasattr(self, '_static_path'):
            root = self.settings.get('static_root', 'static')
            path = os.path.join(self.base_path, root)
            setattr(self, '_static_path', path)
        return getattr(self, '_static_path')
    @property
    def static_url(self):
        if not hasattr(self, '_static_url'):
            url = self.settings.get('static_url', '/static/')
            setattr(self, '_static_url', url)
        return getattr(self, '_static_url')
    @property
    def static_domain(self):
        if not hasattr(self, '_static_domain'):
            domain = self.settings.get('static_domain', '/static')
            setattr(self, '_static_domain', domain)
        return getattr(self, '_static_domain')
    def set_url_root(self, url_root):
        #url_root = self.settings.get('url_root', '/')
        self.app.url_root = self.url_root = url_root
        from torweb.urls import Url
        self.app.url = Url(url_root)
    @property
    def cache(self):
        if not hasattr(self, '_cache'):
            from torweb.cache import MemcachedCache, NullCache
            cache_servers = self.settings.get('memcached', None)
            if cache_servers:
                cache = MemcachedCache(cache_servers)
                setattr(self, '_cache', cache)
            else:
                nullcache = NullCache()
                setattr(self, '_cache', nullcache)
            pass
        return getattr(self, '_cache')
    @property
    def session_store(self):
        sessionstore_name = self.settings.get('session_store', 'MemorySessionStore')
        module = __import__('torweb.sessions', {}, {}, sessionstore_name) 
        cls =  getattr(module, sessionstore_name)
        #import logging
        #logging.info('session store: %s' % cls.__name__)
        if cls.__name__ == 'MemcachedSessionStore':
            #print 'session store: %s' % cls.__name__
            return cls(self.settings.get('memcached', ['127.0.0.1:11211']))
        if cls.__name__ == 'RedisSessionStore':
            _redis = self.settings.get("redis", {})
            import redis
            redis_conn = redis.StrictRedis(host=_redis.get("host", "127.0.0.1"), port=_redis.get("port", "6379"), db="test")
            #return cls(redis.get("host", "127.0.0.1"), redis.get("port", "6379"))
            return cls(redis_conn, key_prefix=_redis.get("prefix", "session"), expire=_redis.get("expire", 3600))
        if cls.__name__ == 'MemorySessionStore':
            #print 'session store: %s' % cls.__name__
            return cls()
        #print 'session store: default'
        return cls()
    
    def init_store(self):
        schemes = self.settings.get('schemes', {})
        _scheme_dict = {}
        for scheme in schemes:
            #if not hasattr(self.app, scheme.get('storm')):
            key = scheme.get('scheme', '')
            if key not in ['mysql', 'postgre', 'sqlite']: continue
            connection = '%(scheme)s://%(user)s:%(pass)s@%(host)s:%(port)s/%(database_name)s?charset=%(charset)s'\
                    % {'scheme': key,
                       'user': scheme.get('user', ''),
                       'pass': scheme.get('pass', ''),
                       'host': scheme.get('host', ''),
                       'port': scheme.get('port', ''),
                       'database_name': scheme.get('db', ''),
                       'charset': scheme.get('charset', 'utf8')
                      }
            if key == 'sqlite':
                connection = '%(scheme)s:%(database_name)s'\
                    % {'scheme': key,
                       'database_name': os.path.join(self.base_path, scheme.get('db', ''))
                      }
            store = scheme.get("storm", None)
            if store: self.init_storm(store, connection)
            session = scheme.get("sqlalchemy", None)
            if session: dic = self.init_sqlalchemy(scheme, connection); _scheme_dict["%s" % scheme.get("alias", "") or scheme.get("db", "")] = dic
        setattr(self.app, 'sqlalchemy_config', _scheme_dict)
    def init_storm(self, store, connection):
        try:
            import storm
            from storm.locals import create_database
            from torweb.db import CacheStore
            database = create_database(connection)
            cache_store = CacheStore(database)
            setattr(self, store, cache_store)
            setattr(self.app, store, cache_store)
        except Exception as e:
            print e
    def init_sqlalchemy(self, scheme, connection):
        try:
            import sqlalchemy
            from sqlalchemy import create_engine, MetaData
            from sqlalchemy.orm import scoped_session, sessionmaker
            from torweb.db import CacheQuery
            import _mysql_exceptions
            from sqlalchemy import event
            from sqlalchemy.exc import DisconnectionError
            def my_on_checkout(dbapi_conn, connection_rec, connection_proxy):
                try:
                    dbapi_conn.cursor().execute('select now()')
                except _mysql_exceptions.OperationalError:
                    raise DisconnectionError
            
            engine = create_engine(
                connection,
                convert_unicode=True,
                encoding="utf-8",
                pool_recycle=3600*7,
                #echo_pool=True,
                echo=False,
            )
            event.listen(engine, 'checkout', my_on_checkout)
            metadata = MetaData(bind=engine)
            session = scoped_session(sessionmaker(bind=engine, query_cls=CacheQuery))
            sqlalchemy_sessions = [session]
            DB_Session = sessionmaker(bind=engine)
            return {"metadata":metadata, "session":session, "sqlalchemy_sessions":sqlalchemy_sessions}
            #setattr(self.app, 'metadata', metadata)
            #setattr(self.app, scheme.get('sqlalchemy', 'session'), session)
            #setattr(self.app, 'sqlalchemy_sessions', sqlalchemy_sessions)
        except Exception as e:
            print e
