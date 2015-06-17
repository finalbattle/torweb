#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import os
import yaml
import logging
from code import interact

class Yaml_Config(object):
    def __init__(self, base_path, yaml_path, url_root="/"):
        self.yaml_path = yaml_path
        f = open(self.yaml_path)
        self.CONF = CONFIG(self.yaml_path)
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
            from werkzeug.contrib.cache import RedisCache
            
            nullcache = NullCache()
            setattr(self, '_cache', nullcache)
            cache_servers = self.settings.get('memcached', None)
            if cache_servers:
                cache = MemcachedCache(cache_servers)
                setattr(self, '_cache', cache)
            try:
                redis_cache_host = self.CONF("REDIS.HOST")
                redis_cache_port = self.CONF("REDIS.PORT")
                if redis_cache_host and redis_cache_port:
                    cache = RedisCache(redis_cache_host, redis_cache_port)
                    setattr(self, '_cache', cache)
                    logging.info("cache: RedisCache")
            except KeyError:
                pass
            #cache_servers = self.settings.get('memcached', None)
            #if cache_servers:
            #    cache = MemcachedCache(cache_servers)
            #    setattr(self, '_cache', cache)
            #else:
            #    nullcache = NullCache()
            #    setattr(self, '_cache', nullcache)
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
            redis_conn = redis.StrictRedis(host=_redis.get("host", "127.0.0.1"), port=_redis.get("port", 6379), db="test")
            return cls(redis_conn, key_prefix=_redis.get("prefix", "session"), expire=_redis.get("expire", 3600))
        if cls.__name__ == 'RedisSessionStoreNew':
            _redis = self.settings.get("redis", {})
            import redis
            from torweb.sessions import RedisPool
            redis_pool = RedisPool(_redis.get("host", "127.0.0.1"), _redis.get("port", 6379), _redis.get("expire", 3600))
            return cls(redis_pool.get_redis(), key_prefix=_redis.get("prefix", cls.__name__), expire=_redis.get("expire", 3600))
        if cls.__name__ == 'MemorySessionStore':
            #print 'session store: %s' % cls.__name__
            return cls()
        #print 'session store: default'
        return cls()
    
    def init_store(self, schemes_list=[]):
        schemes = self.settings.get('schemes', schemes_list)
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
            session = scoped_session(sessionmaker(bind=engine, query_cls=CacheQuery,expire_on_commit=False))
            sqlalchemy_sessions = [session]
            DB_Session = sessionmaker(bind=engine)
            return {"metadata":metadata, "session":session, "sqlalchemy_sessions":sqlalchemy_sessions}
            #setattr(self.app, 'metadata', metadata)
            #setattr(self.app, scheme.get('sqlalchemy', 'session'), session)
            #setattr(self.app, 'sqlalchemy_sessions', sqlalchemy_sessions)
        except Exception as e:
            print e

import re
import logging

inner_pattern = re.compile('\{\w+[\.\w+]*\}')

class ConfigLoader(object):
    config_path = None
    base_path = ""

    def __init__(self):
        self.config = None

    def load_environment(self):
        self.config['project_path'] = self.base_path

    def get_config_path(self):
        if not ConfigLoader.config_path:
            ConfigLoader.config_path = os.path.join(self.base_path, 'config')
        return ConfigLoader.config_path

    def get_config_file(self, name):
        import os.path

        #return os.path.join(self.get_config_path(), '%s.yaml' % name)
        return os.path.join(self.get_config_path(), '%s' % name)

    def load(self, config_file):
        self.config = self.load_file(config_file)
        self.load_environment()
        self.load_dynamic(self.config)
        return self.config
    def load_path(self, config_path):
        self.config = self.load_file(config_path)
        self.load_environment()
        self.load_dynamic(self.config)
        return self.config

    def load_file(self, config_file):
        config = {}
        try:
            with open(self.get_config_file(config_file), 'rb') as f:
                config = yaml.load(f)
                self.load_import(config)
        except Exception:
            logging.error("Uncaught Exception in load_file", exc_info=True)
        return config

    def load_dynamic(self, config):
        for key, value in config.iteritems():
            if isinstance(value, dict):
                self.load_dynamic(value)
                continue

            if not isinstance(value, basestring):
                continue

            matches = inner_pattern.findall(value)
            if not matches:
                continue
            while matches:
                for match in matches:
                    config[key] = re.sub(match, str(self.getConfig(match[1:-1])), config[key])
                matches = inner_pattern.findall(config[key])

    def load_import(self, config):
        if not 'import' in config:
            return config
        import_files = config['import']
        if import_files and (isinstance(import_files, set) or isinstance(import_files, list)):
            for import_file in import_files:
                self.import_single(config, import_file)
        return config

    def combile(self, config, import_config):
        for key, value in import_config.iteritems():
            if key == 'import' and 'import' in config:
                config['import'].extend(value)
                continue

            if not key in config:
                config[key] = value
            elif isinstance(value, dict) and isinstance(config[key], dict):
                self.combile(config[key], value)

    def import_single(self, config, import_file):
        import_config = self.load_file(import_file)
        self.combile(config, import_config)
        return config

    def getConfig(self, key):
        # every key is upper case
        key_no_case = key.lower()
        # split the string by .
        subkeys = re.split(r'\.', key_no_case)
        current_config = self.config
        for subkey in subkeys:
            assert (current_config is not None and isinstance(current_config, dict))
            current_config = current_config[subkey]
        return current_config

def get_host_ip(eth="eth0"):
    ip_addr = None
    import platform

    try:
        if platform.system() == 'Windows':
            import socket
            ip_addr = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        # 暂时将mac等同于linxu
        else:
            import fcntl
            import struct
            import socket
            def get_ip_address(ifname):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                return socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(),
                    0x8915, # SIOCGIFADDR
                    struct.pack('256s', ifname[:15])
                )[20:24])

            ip_addr = get_ip_address(eth)
    except Exception as e:
        logging.error(e)

    return ip_addr


class Configuration(object):
    config_context = None

    def __init__(self, config_path):
        if not self.config_context:
            #self.config_context = ConfigLoader().load(config_entry_file)
            self.config_context = ConfigLoader().load_path(config_path)

    def getConfig(self, key):
        #Configuration.init()
        # every key is upper case
        key_no_case = key.lower()
        # split the string by .
        subkeys = re.split(r'\.', key_no_case)
        current_config = self.config_context
        for subkey in subkeys:
            assert (current_config is not None and isinstance(current_config, dict))
            current_config = current_config[subkey]
        return current_config


#configuration = Configuration()
#def CONF(key):
#    """
#     get the configuration value
#    """
#    return configuration.getConfig(key)
#    #return Configuration.getConfig(key)

class CONFIG(object):
    configuration = None
    def __init__(self, path):
        self.configuration = Configuration(path)
    def __call__(self, key):
        return self.configuration.getConfig(key)
