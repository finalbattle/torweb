#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

__all__ = ["get_modules", "WebApplication", "WSGIApplication", "DebugApplication", "make_application"]

import os
import re
import logging
import tornado.options
from tornado.web import (Application, RequestHandler, StaticFileHandler as _StaticFileHandler,
                         RedirectHandler, HTTPError, URLSpec)
import tornado.wsgi
from tornado.wsgi import WSGIApplication as _WSGIApplication
from torweb.urls import url
from torweb.config import Yaml_Config
#from torweb.handlers import StaticFileHandler, ErrorHandler, WSGIRequest
from torweb.handlers import StaticFileHandler, ErrorHandler
from torweb import base_path
from code import interact


def get_modules(prefix, parent):
    if not os.path.isfile(os.path.join(parent, '__init__.py')):
        return
    for pathname in os.listdir(parent):
        child = os.path.join(parent, pathname)
        if pathname.startswith('.'):
            continue
        elif pathname == '__init__.py':
            yield '.'.join(prefix), pathname.split('.')[0]
        elif os.path.isdir(child):
            for i in get_modules(prefix+[pathname], child):
                yield i, pathname.split('.')[0]
        elif os.path.isfile(child) and pathname.endswith('.py'):
            yield '.'.join(prefix+[pathname[:-3]]), pathname.split('.')[0]


class WebApplication(Application):
    def __call__(self, request): 
        #print """Called by HTTPServer to execute the request."""
        #print "##################################################"
        if not hasattr(self, "add_slash"):
            setattr(self, "add_slash", False)
        _add_slash = getattr(self, "add_slash")
        transforms = [t(request) for t in self.transforms]
        handler = None
        args = []
        kwargs = {}
        if _add_slash == False:
            # removeslash
            if request.path.endswith("/"):
                if request.method in ("GET", "HEAD"):
                    uri = request.path.rstrip("/")
                    if uri:  # don't try to redirect '/' to ''
                        if request.query:
                            uri += "?" + request.query
                        hdr = RedirectHandler(self, request, url=uri)
                        hdr._execute(transforms, *args, **kwargs)
                        return hdr
                else:
                    raise HTTPError(404)
        else:
            # addslash
            li = [_compile for _compile in self._static_urls if re.compile(_compile).match(request.path)]
            if len(li) == 0 and not request.path.endswith("/"):
                if request.method in ("GET", "HEAD"):
                    uri = request.path + "/"
                    if request.query:
                        uri += "?" + request.query
                    hdr = RedirectHandler(self, request, url=uri)
                    hdr._execute(transforms, *args, **kwargs)
                    return hdr
                raise HTTPError(404)
        super(WebApplication, self).__call__(request)


class WSGIApplication(_WSGIApplication):
    def __call__(self, environ):
        handler = web.Application.__call__(self, tornado.wsgi.HTTPRequest(environ))
        assert handler._finished
        status = str(handler._status_code) + " " + \
            httplib.responses[handler._status_code]
        headers = handler._headers.items()
        if hasattr(handler, "_new_cookie"):
            for cookie in handler._new_cookie.values():
                headers.append(("Set-Cookie", cookie.OutputString(None)))
        start_response(status,
                       [(native_str(k), native_str(v)) for (k, v) in headers])
        return handler._write_buffer


class DebugApplication(WebApplication):
    "Tornado Application supporting werkzeug interactive debugger."
 
    # This supports get_error_html in Handler above.
 
    def __init__(self, *args, **kwargs):
        from werkzeug.debug import DebuggedApplication
        self.debug_app = DebuggedApplication(self.debug_wsgi_app, evalex=True)
        self.debug_container = tornado.wsgi.WSGIContainer(self.debug_app)
        super(DebugApplication, self).__init__(*args, **kwargs)
 
    def __call__(self, request):
        if '__debugger__' in request.uri:
            # Do not call get_current_traceback here, as this is a follow-up
            # request from the debugger. DebugHandler loads the traceback.
            return self.debug_container(request)
        return super(DebugApplication, self).__call__(request)
 
    @classmethod
    def debug_wsgi_app(cls, environ, start_response):
        print "Fallback WSGI application, wrapped by werkzeug's debug middleware."
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return ['Failed to load debugger.\n']
 
    def get_current_traceback(self):
        "Get the current Python traceback, keeping stack frames in debug app."
        traceback = get_current_traceback()
        for frame in traceback.frames:
            self.debug_app.frames[frame.id] = frame
        self.debug_app.tracebacks[traceback.id] = traceback
        return traceback
 
    def get_traceback_renderer_keywords(self):
        "Keep consistent debug app configuration."
        # DebuggedApplication generates a secret for use in interactions.
        # Otherwise, an attacker could inject code into our application.
        # Debugger gives an empty response when secret is not provided.
        return dict(evalex=self.debug_app.evalex, secret=self.debug_app.secret)

def get_current_traceback():
    "Get the current traceback in debug mode, using werkzeug debug tools."
    # Lazy import statement, as debugger is only used in development.
    from werkzeug.debug.tbtools import get_current_traceback
    # Experiment with skip argument, to skip stack frames in traceback.
    traceback = get_current_traceback(skip=2, show_hidden_frames=False,
                                      ignore_system_exceptions=True)
    return traceback

 
def make_application(app, debug=False, wsgi=False, settings_path="", url_root="/", **keywords):
    app_path = os.path.abspath(os.path.dirname(app.__file__))
    conf = None
    if settings_path != "":
        #conf = app.settings
        conf = Yaml_Config(app_path, settings_path, url_root=url_root)
        setattr(app, 'yaml_conf', conf)
        #logging.info(url_root)
    #else:
    #    conf = Yaml_Config(app_path, os.path.join(app_path, 'settings.yaml'), url_root=url_root)
    views_path = os.path.join(app_path, 'views')
    module_list = []
    def getModule(module):
        if type(module) == tuple:
            return getModule(module[0])
        else:
            return module

    for module, name in get_modules([app.__name__, 'views'], views_path):
        module = getModule(module)
        #if type(module) == tuple:
        #    module = module[0]
        #    if type(module) == tuple:
        #        module = module[0]
        m = __import__(module, {}, {}, name)
        module_list.append(m)
    from torweb.urls import url_rules, except_url, url404
    def _set_debug(kw):
        kw["debug"] = debug
        return kw
    url_handlers = []
    url_rules.extend(url404.handlers)
    app_url_handlers = url_rules
    url_handlers.extend(app_url_handlers)
    url_handlers.extend(except_url.handlers)
    #url_handlers = [URLSpec(spec.regex.pattern, spec.handler_class, _set_debug(spec.kwargs), spec.name) for spec in url_handlers]
    _static_urls = [spec.regex.pattern for spec in url.handlers if spec.kwargs.has_key("path") and hasattr(spec.handler_class, 'static_handler') and spec.handler_class.static_handler==True]

    #for _uri in url_handlers:
    #    logging.info("%s <name:%s>" % (_uri.regex.pattern, _uri.name))

    keywords.update({"debug":debug})
    if debug:
        application = DebugApplication(url_handlers, **keywords)
    else:
        if wsgi == True:
            application = _WSGIApplication(url_handlers, **keywords)
        else:
            application = WebApplication(url_handlers, **keywords)
    application.url_handlers = url_handlers
    application._static_urls = _static_urls
    # 初始化session store
    if conf:
        application.session_store = conf.session_store
    else:
        from torweb.sessions import MemorySessionStore
        application.session_store = MemorySessionStore()
    return application

class InitializeApplication(object):
    def __init__(self, app):
        self.app = app
        self.app_path = os.path.abspath(os.path.dirname(app.__file__))
        self.conf = Yaml_Config(os.path.join(app_path, 'settings.yaml'))
        pass
    def make_application(self, debug, wsgi):
        return make_application(self.app, debug, wsgi)
