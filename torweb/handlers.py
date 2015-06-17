#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import os
import traceback
from tornado.web import (RequestHandler, StaticFileHandler as _StaticFileHandler,
                         ErrorHandler as _ErrorHandler, HTTPError
                        )
from tornado.wsgi import HTTPRequest
from torweb.wrappers import cached_property
from torweb.sessions import SessionStore
from torweb.datastructure import MultiDict, ImmutableMultiDict
from code import interact

__all__ = ['BaseHandler', 'StaticFileHandler', 'ErrorHandler', 'XMLRPCHandler', 'JSONRPCHandler', 'WSGIRequest']


class BaseHandler(RequestHandler):

    def initialize(self, debug=False, **kwargs):
        self.debug = debug
        self.kwargs = kwargs

    def prepare(self):
        '''
        before request
        '''
        if self.debug:
            self.get_error_html = self.get_debugger_html
        super(BaseHandler, self).prepare()
        #print 'before request'
    #def initialize(self, debug):
    #    # Since we are using the same Handler class for both debug and normal
    #    # modes, we check for debug flag here. Alternatively, define
    #    # get_error_html in a subclass and pass that class to the Application
    #    # on instantiation.
    #    if debug:
    #        self.get_error_html = self.get_debugger_html

    def write_error(self, status_code, **kwargs):
        """Override to implement custom error pages.

        ``write_error`` may call `write`, `render`, `set_header`, etc
        to produce output as usual.

        If this error was caused by an uncaught exception (including
        HTTPError), an ``exc_info`` triple will be available as
        ``kwargs["exc_info"]``.  Note that this exception may not be
        the "current" exception for purposes of methods like
        ``sys.exc_info()`` or ``traceback.format_exc``.

        For historical reasons, if a method ``get_error_html`` exists,
        it will be used instead of the default ``write_error`` implementation.
        ``get_error_html`` returned a string instead of producing output
        normally, and had different semantics for exception handling.
        Users of ``get_error_html`` are encouraged to convert their code
        to override ``write_error`` instead.
        """
        if hasattr(self, 'get_error_html'):
            if 'exc_info' in kwargs:
                exc_info = kwargs.pop('exc_info')
                kwargs['exception'] = exc_info[1]
                try:
                    # Put the traceback into sys.exc_info()
                    raise_exc_info(exc_info)
                except Exception:
                    self.finish(self.get_error_html(status_code, **kwargs))
            else:
                self.finish(self.get_error_html(status_code, **kwargs))
            return

        if self.settings.get("debug") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            self.set_header('Content-Type', 'text/plain')
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish()
        else:
            self.finish("<html><title>%(code)d: %(message)s</title>"
                        "<body>%(code)d: %(message)s</body></html>" % {
                            "code": status_code,
                            "message": self._reason,
                        })
 
    def get_debugger_html(self, status_code, **kwargs):
        if self.debug:
            from torweb.application import DebugApplication
            assert isinstance(self.application, DebugApplication)
            traceback = self.application.get_current_traceback()
            keywords = self.application.get_traceback_renderer_keywords()
            html = traceback.render_full(**keywords).encode('utf-8', 'replace')
            return html.replace(b'WSGI', b'tornado')

    @property
    def args(self):
        names = self.request.arguments.keys()
        arguments = {}
        for name in names:
            arguments[name] = self.get_argument(name)
        return arguments

    @property
    def query_args(self):
        cls = ImmutableMultiDict
        result = []
        keys = []
        querys = self.request.query
        querys = querys.split('&')
        for query_str in querys:
            if not query_str:continue
            if '=' in query_str:
                key, value = query_str.split('=')
            else:
                key = query_str; value = u''
            result.append((key, value.decode('utf-8', 'ignore')))
        return cls(result)

    def on_finish(self):
        '''
        after request
        '''
        pass

    @cached_property
    def session(self):
        '''根据session_sid值来获取session对象，或者初始化一个session对象'''
        session_store = self.application.session_store
        sid = self.cookies.get('session_id')
        #print "sid--> %s" % sid
        if session_store.__class__.__name__ == 'RedisSessionStore':
            if sid is None:
                _sessionsid = self.application.session_store.generate_sid()
                #print "cookie generate_sid--%s" % _sessionsid
            else:
                _sessionsid = sid.value
                #print "cookie sessionsid--%s" % _sessionsid
            from torweb.sessions import RedisSession
            return RedisSession(self.application.session_store, _sessionsid)
        if session_store.__class__.__name__ == 'RedisSessionStoreNew':
            if sid is None:
                _sessionsid = self.application.session_store.generate_sid()
                #print "cookie generate_sid--%s" % _sessionsid
            else:
                _sessionsid = sid.value
                #print "cookie sessionsid--%s" % _sessionsid
            from torweb.sessions import RedisSession
            return RedisSession(self.application.session_store, _sessionsid)
        else:
            #print "session_store -- %s" % session_store
            if sid is None:
                return session_store.new()
            else:
                return session_store.get(sid.value)
            #sessionsid = self.cookies.get("session_id")

    def save_session(self):
        '''返回response之前，向客户端写入cookie
        保存session_sid到cookie
        '''
        try:
            self.set_cookie('session_id', self.session.sid, expires_days=3650)
        except AttributeError:
            pass
        if self.session.should_save:
            self.application.session_store.save(self.session)

    def write_jsonp(self, obj):
        key = self.get_argument("callback", u"jsonpcallback")
        try:
            from simplejson import dumps
        except:
            from json import dumps
        s = dumps(obj)
        self.set_header("Content-Type", "application/json")
        self.write(key+u'(' + s + u')')

class StaticFileHandler(_StaticFileHandler):

    def initialize(self, path, default_filename=None, debug=False, **kwargs):
        super(StaticFileHandler, self).initialize(path, default_filename)
        self.debug = debug
        self.kwargs = kwargs
    static_handler = True

class ErrorHandler(_ErrorHandler): 
    """Generates an error response with status_code for all requests.""" 

    def __init__(self, application, request, status_code): 
        RequestHandler.__init__(self, application, request)
        self.set_status(status_code) 

    def initialize(self, app=None, request=None, status_code=404):
        self.app = app; self.status_code = status_code

    def prepare(self): 
        raise HTTPError(self._status_code)

#    def get_error_html(self, status_code, **kwargs): 
#        from ivtime import base_path
#        return open(os.path.join(base_path,'static', 'error','404.html')).read() 

def private(func):
    # Decorator to make a method, well, private.
    class PrivateMethod(object):
        def __init__(self):
            self.private = True
        __call__ = func
    return PrivateMethod()

class XMLRPCHandler(BaseHandler):

    def get(self):
        pass

    def post(self):
        import xmlrpclib
        try:
            params, method_name = xmlrpclib.loads(self.request.body)
        except:
            # Bad request formatting, bad.
            raise Exception('Deal with how you want.')
        if method_name in dir(RequestHandler):
            # Pre-existing, not an implemented attribute
            raise AttributeError('%s is not implemented.' % method_name)
        try:
            method = getattr(self, method_name)
        except:
            # Attribute doesn't exist
            raise AttributeError('%s is not a valid method.' % method_name)
        if not callable(method):
            # Not callable, so not a method
            raise Exception('Attribute %s is not a method.' % method_name)
        if method_name.startswith('_') or \
                ('private' in dir(method) and method.private is True):
            # No, no. That's private.
            raise Exception('Private function %s called.' % method_name)
        response = method(*params)
        response_xml = xmlrpclib.dumps((response,), methodresponse=True)
        self.set_header("Content-Type", "text/xml")
        self.write(response_xml)


class JSONRPCHandler(BaseHandler):

    def get(self, *args, **kwargs):
        return self.post()

    def post(self, *args, **kwargs):
        """
            JSON-RPC 2.0
            Request Object:
                {u'jsonrpc': u'2.0', u'params': [1, 2], u'id': u'3ebm619c', u'method': u'add'}
            Response Object:
                {"jsonrpc": "2.0", "result": 3, "id": "3ebm619c"}
        """
        import jsonrpclib
        try:
            json_request = jsonrpclib.loads(self.request.body)
            params = json_request.get("params", [])
            method_name = json_request.get("method", "")
        except:
            # Bad request formatting, bad.
            raise Exception('Deal with how you want.')
        if method_name in dir(RequestHandler):
            # Pre-existing, not an implemented attribute
            raise AttributeError('%s is not implemented.' % method_name)
        try:
            method = getattr(self, method_name)
        except:
            # Attribute doesn't exist
            raise AttributeError('%s is not a valid method.' % method_name)
        if not callable(method):
            # Not callable, so not a method
            raise Exception('Attribute %s is not a method.' % method_name)
        if method_name.startswith('_') or \
                ('private' in dir(method) and method.private is True):
            # No, no. That's private.
            raise Exception('Private function %s called.' % method_name)
        response = method(*params)
        response_json = jsonrpclib.dumps(response, methodresponse=True, rpcid=json_request["id"])
        self.set_header("Content-Type", "text/json")
        self.write(response_json)


class WSGIRequest(HTTPRequest):
    def __init__(self, env):
        super(WSGIRequest, self).__init__(env)
        #HTTPRequest.__init__(env)
        self.environ = env
