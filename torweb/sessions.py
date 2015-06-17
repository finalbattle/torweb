#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>
import os
import re
import sys
import tempfile
from os import path
from time import time
from random import random

try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1
try:
    from cPickle import dumps, loads, HIGHEST_PROTOCOL
except ImportError:
    from pickle import dumps, loads, HIGHEST_PROTOCOL

_sha1_re = re.compile(r'^[a-f0-9]{40}$')

def _urandom():
    if hasattr(os, 'urandom'):
        return os.urandom(30)
    return random()

def generate_key(salt=None):
    return sha1('%s%s%s' % (salt, time(), _urandom())).hexdigest()

class UpdateDictMixin(object):
    """Makes dicts call `self.on_update` on modifications.

    .. versionadded:: 0.5

    :private:
    """

    on_update = None

    def calls_update(name):
        def oncall(self, *args, **kw):
            rv = getattr(super(UpdateDictMixin, self), name)(*args, **kw)
            if self.on_update is not None:
                self.on_update(self)
            return rv
        oncall.__name__ = name
        return oncall

    __setitem__ = calls_update('__setitem__')
    __delitem__ = calls_update('__delitem__')
    clear = calls_update('clear')
    pop = calls_update('pop')
    popitem = calls_update('popitem')
    setdefault = calls_update('setdefault')
    update = calls_update('update')
    del calls_update

class CallbackDict(UpdateDictMixin, dict):
    """A dict that calls a function passed every time something is changed.
    The function is passed the dict instance.
    """

    def __init__(self, initial=None, on_update=None):
        dict.__init__(self, initial or ())
        self.on_update = on_update

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            dict.__repr__(self)
        )

class ModificationTrackingDict(CallbackDict):
    __slots__ = ('modified',)

    def __init__(self, *args, **kwargs):
        def on_update(self):
            self.modified = True
        self.modified = False
        CallbackDict.__init__(self, on_update=on_update)
        dict.update(self, *args, **kwargs)

    def copy(self):
        """Create a flat copy of the dict."""
        missing = object()
        result = object.__new__(self.__class__)
        for name in self.__slots__:
            val = getattr(self, name, missing)
            if val is not missing:
                setattr(result, name, val)
        return result

    def __copy__(self):
        return self.copy()

class Session(ModificationTrackingDict):
    """Subclass of a dict that keeps track of direct object changes.  Changes
    in mutable structures are not tracked, for those you have to set
    `modified` to `True` by hand.
    """
    __slots__ = ModificationTrackingDict.__slots__ + ('sid', 'new')

    def __init__(self, data, sid, new=False):
        ModificationTrackingDict.__init__(self, data)
        self.sid = sid
        self.new = new

    def __repr__(self):
        return '<%s %s%s>' % (
            self.__class__.__name__,
            dict.__repr__(self),
            self.should_save and '*' or ''
        )

    @property
    def should_save(self):
        """True if the session should be saved.

        .. versionchanged:: 0.6
           By default the session is now only saved if the session is
           modified, not if it is new like it was before.
        """
        return self.modified


class SessionStore(object):
    """Baseclass for all session stores.  The Werkzeug contrib module does not
    implement any useful stores besides the filesystem store, application
    developers are encouraged to create their own stores.

    :param session_class: The session class to use.  Defaults to
                          :class:`Session`.
    """

    def __init__(self, session_class=None):
        if session_class is None:
            session_class = Session
        self.session_class = session_class

    def is_valid_key(self, key):
        """Check if a key has the correct format."""
        return _sha1_re.match(key) is not None

    def generate_key(self, salt=None):
        """Simple function that generates a new session key."""
        return generate_key(salt)

    def new(self):
        """Generate a new session."""
        return self.session_class({}, self.generate_key(), True)

    def save(self, session):
        """Save a session."""

    def save_if_modified(self, session):
        """Save if a session class wants an update."""
        if session.should_save:
            self.save(session)

    def delete(self, session):
        """Delete a session."""

    def get(self, sid):
        """Get a session for this sid or a new session object.  This method
        has to check if the session key is valid and create a new session if
        that wasn't the case.
        """
        return self.session_class({}, sid, True)


class MemorySessionStore(SessionStore):
    def __init__(self, session_class=Session):
        SessionStore.__init__(self, session_class)
        self.db = {}

    def save(self, session):
        self.db[session.sid] = session

    def delete(self, session):
        self.db.pop(session.sid, None)

    def get(self, sid):
        try:
            return self.db[sid]
        except KeyError:
            return self.new()


class MemcachedSessionStore(SessionStore):
    def __init__(self, servers, session_class=Session):
        SessionStore.__init__(self, session_class)
        try:
            import cmemcache as memcache
        except ImportError:
            import memcache
        self.client = memcache.Client(servers)

    def save(self, session):
        s = dumps(dict(session), HIGHEST_PROTOCOL)
        self.client.set(str(session.sid), s)

    def delete(self, session):
        self.client.delete(str(session.sid))

    def get(self, sid):
        data = self.client.get(str(sid))
        if data is None:
            return self.session_class({}, sid, False)
        else:
            return self.session_class(loads(data), sid, False)

#class RedisSessionStore(SessionStore):
#    def __init__(self, server="127.0.0.1", port=6379, timeout=30, session_class=Session):
#        SessionStore.__init__(self, session_class)
#        import redis
#        redis_pool = redis.ConnectionPool(host=server,
#                        port=port, db=0,socket_timeout=timeout)
#        self.client = redis.Redis(redis_pool)
#
#    def save(self, session):
#        s = dump(dict(session), HIGHEST_PROTOCOL)
#        self.client.set(str(session.sid), s)
#        self.client.expire(self.session.sid, 300)
#
#    def delete(self, session):
#        self.client.delete(str(session.sid))
#
#    def get(self, sid):
#        from code import interact
#        interact(local=locals())
#        data = self.client.get(str(sid))
#        if data is None:
#            return self.session_class({}, sid, False)
#        else:
#            return self.session_class(loads(data), sid, False)

import cPickle as pickle
from uuid import uuid4
from code import interact
import redis
class RedisPool(object):
    
    _pool = None

    def __init__(self, host, port, timeout=0):
        self.host = host
        self.port = port
        self.timeout = timeout
    def get_pool(self):
        if not RedisPool._pool:
            RedisPool.pool = redis.ConnectionPool(host=self.host,
                port=self.port, db=0,socket_timeout=self.timeout)
        return RedisPool.pool

    def get_redis(self):
        return redis.Redis(connection_pool=self.get_pool())

    
    def _ensure__pool(self):
        if not RedisPool._pool:
            RedisPool.get_pool()
    
    def get_conn(self):
        self._ensure__pool()
        return redis.Redis(connection_pool=self._pool)
    
    def get_pconn(self):
        self._ensure__pool()
        return redis.Redis(connection_pool=self._pool).pipeline()
        # 可以在一次请求中执行多个set命令，这样避免了多次的往返时延

    def clear_rd(self):
        """清空redis数据"""
        rd = self.get_conn()
        r1 = str(rd.dbsize())
        rd.flushdb()
        r2 = str(rd.dbsize())
        #Config.logger.info("已清空redis数据，清空前：%s，清空后：%s" % (r1, r2,))
        print ("已清空redis数据，清空前：%s，清空后：%s" % (r1, r2,))
        
    def clear_rd_keys(self, *patterns):
        """清空redis数据"""
        rd = self.get_conn()
        r1 = str(rd.dbsize())
        for pt in patterns:
            keys = rd.keys(pt)
            for key in keys:
                rd.delete(key)
        r2 = str(rd.dbsize())
        #Config.logger.info("已清空redis %s相关数据，清空前：%s，清空后：%s" % (patterns, r1, r2,))
        print ("已清空redis %s相关数据，清空前：%s，清空后：%s" % (patterns, r1, r2,))

#def get_redis():
#    return RedisPool.get_redis()

class RedisSessionStoreNew:
 
    def __init__(self, redis_pool, **options):
        self.options = {
            'key_prefix': 'RedisSessionStoreNew',
            'expire': 7200,
        }
        self.options.update(options)
        self.redis = redis_pool
 
    def prefixed(self, sid):
        print '%s:%s' % (self.options['key_prefix'], sid)
        return '%s:%s' % (self.options['key_prefix'], sid)
 
    def generate_sid(self, salt=None):
        return generate_key(salt)
#        return uuid4().get_hex()
 
    def get_session(self, sid, name):
        data = self.redis.hget(self.prefixed(sid), name)
        session = pickle.loads(data) if data else dict()
        print "RedisSessionStore--get_session--session", session
        return session
 
    def set_session(self, sid, session_data, name):
        expiry = self.options['expire']
        self.redis.hset(self.prefixed(sid), name, pickle.dumps(session_data))
        if expiry:
            self.redis.expire(self.prefixed(sid), expiry)
        print "save session: set_session--%s-%s-%s" % (sid, session_data, name)
    def save(self, session):
        session._save()
        print "save"
 
    def delete_session(self, sid):
        self.redis.delete(self.prefixed(sid))


class RedisSessionStore:
 
    def __init__(self, redis_connection, **options):
        self.options = {
            'key_prefix': 'session',
            'expire': 7200,
        }
        self.options.update(options)
        self.redis = redis_connection

    def prefixed(self, sid):
        return '%s:%s' % (self.options['key_prefix'], sid)

    def generate_sid(self, salt=None):
        return generate_key(salt)
#        return uuid4().get_hex()

    def get_session(self, sid, name):
        data = self.redis.hget(self.prefixed(sid), name)
        session = pickle.loads(data) if data else dict()
        return session

    def set_session(self, sid, session_data, name):
        expiry = self.options['expire']
        self.redis.hset(self.prefixed(sid), name, pickle.dumps(session_data))
        if expiry:
            self.redis.expire(self.prefixed(sid), expiry)
        #print "save session: set_session--%s-%s-%s" % (sid, session_data, name)

    def save(self, session):
        session._save()

    def delete_session(self, sid):
        self.redis.delete(self.prefixed(sid))


class RedisSession(Session):
    def __init__(self, session_store, sessionid=None):
        self._store = session_store
        self._sessionid = sessionid if sessionid else self._store.generate_sid()
        self._sessiondata = self._store.get_session(self._sessionid, 'data')
        super(RedisSession, self).__init__(self._sessiondata, self._sessionid)
        self.dirty = False
 
    def clear(self):
        self._store.delete_session(self._sessionid)
 
    def access(self, remote_ip):
        access_info = {'remote_ip':remote_ip, 'time':'%.6f' % time()}
        self._store.set_session(
                self._sessionid,
                'last_access',
                pickle.dumps(access_info)
                )
 
    def last_access(self):
        access_info = self._store.get_session(self._sessionid, 'last_access')
        return pickle.loads(access_info)
 
    @property
    def sessionid(self):
        return self._sessionid
 
    def __getitem__(self, key):
        return self._sessiondata[key]
 
    def __setitem__(self, key, value):
        self._sessiondata[key] = value
        self._dirty()
 
    def __delitem__(self, key):
        del self._sessiondata[key]
        self._dirty()
 
    def __len__(self):
        return len(self._sessiondata)
 
    def __contains__(self, key):
        return key in self._sessiondata
 
    def __iter__(self):
        for key in self._sessiondata:
            yield key
 
    def __repr__(self):
        return self._sessiondata.__repr__()
 
    def __del__(self):
        if self.dirty:
            self._save()
 
    def _dirty(self):
        self.dirty = True
        print "dirty:", self.dirty
 
    def _save(self):
        self._store.set_session(self._sessionid, self._sessiondata, 'data')
        self.dirty = False
    @property
    def should_save(self):
        """True if the session should be saved.

        .. versionchanged:: 0.6
           By default the session is now only saved if the session is
           modified, not if it is new like it was before.
        """
        return self.dirty

    def get(self, key, default_value=None):
        try:
            return self[key]
        except KeyError:
            return default_value
        # return self._sessiondata[key]


#try:
#    import pymongo
#
#    class MongoDBSession(BaseSession):
#        """Class implementing the MongoDB based session storage.
#        All sessions are stored in a collection "tornado_sessions" in the db
#        you specify in the session_storage setting.
#
#        The session document structure is following:
#        'session_id': session ID
#        'data': serialized session object
#        'expires': a timestamp of when the session expires, in sec since epoch
#        'user_agent': self-explanatory
#        An index on session_id is created automatically, on application's init.
#
#        The end_request() is called after every operation (save, load, delete),
#        to return the connection back to the pool.
#        """
#
#        def __init__(self, db, **kwargs):
#            super(MongoDBSession, self).__init__(**kwargs)
#            self.db = db # an instance of pymongo.collection.Collection
#            if not kwargs.has_key('session_id'):
#                self.save()
#
#        @staticmethod
#        def _parse_connection_details(details):
#            # mongodb://[host[:port]]/db
#            if details[10] != '/':
#                # host and port specified
#                match = re.match('mongodb://([\S|\.]+?)?(?::(\d+))?/(\S+)', details)
#                host = match.group(1)
#                port = int(match.group(2))
#                database = match.group(3)
#            else:
#                # default host and port
#                host = 'localhost'
#                port = 27017
#                match = re.match('mongodb:///(\S+)', details)
#                database = match.group(1)
#
#            return host, port, database
#
#        def save(self):
#            """Upsert a document to the tornado_sessions collection.
#            The document's structure is like so:
#            {'session_id': self.session_id,
#             'data': self.serialize(),
#             'expires': self._serialize_expires(),
#             'user_agent': self.user_agent}
#            """
#            # upsert
#            self.db.update(
#                {'session_id': self.session_id}, # equality criteria
#                {'session_id': self.session_id,
#                 'data': self.serialize(),
#                 'expires': self._serialize_expires(),
#                 'user_agent': self.user_agent}, # new document
#                upsert=True)
#            self.db.database.connection.end_request()
#
#        @staticmethod
#        def load(session_id, db):
#            """Load session from the storage."""
#            try:
#                data = db.find_one({'session_id': session_id})
#                if data:
#                    kwargs = MongoDBSession.deserialize(data['data'])
#                    db.database.connection.end_request()
#                    return MongoDBSession(db, **kwargs)
#                db.database.connection.end_request()
#                return None
#            except:
#                db.database.connection.end_request()
#                return None
#
#        def delete(self):
#            """Remove session from the storage."""
#            self.db.remove({'session_id': self.session_id})
#            self.db.database.connection.end_request()
#
#        @staticmethod
#        def delete_expired(db):
#            db.remove({'expires': {'$lte': int(time.time())}})
#
#except ImportError:
#    pass
