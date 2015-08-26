#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import logging
import tornado
import tornado.autoreload
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer
from datetime import datetime
from code import interact
from tornado.options import define, options

define("cmd", default="runserver", metavar="runserver|urls")
define("port", default=8888)

tornado.options.parse_command_line()

def run(app, host='0.0.0.0', port=''):
    import tornado
    instance = IOLoop.instance()
    if app.settings['debug'] == True:
        if tornado.version_info[0] < 4:
            http = HTTPServer(app, xheaders=True)
        else:
            import tornado.httpserver
            from werkzeug.debug import DebuggedApplication
            wsgi_application = tornado.wsgi.WSGIAdapter(app)
            debug_app = DebuggedApplication(app=wsgi_application, evalex=True)
            app.debug_app = debug_app
            debug_container = tornado.wsgi.WSGIContainer(debug_app)
            http = tornado.httpserver.HTTPServer(debug_container)
        tornado.autoreload.start(instance)
        logging.info('- [%s restart with reload]' % (app.__class__.__name__))
    else:
        if hasattr(app, "_wsgi") and app._wsgi == True:
            container = WSGIContainer(app)
            http = HTTPServer(container)
        else:
            tornado.autoreload.start(instance)
            logging.info('- [%s restart with reload]' % (app.__class__.__name__))
            http = HTTPServer(app, xheaders=True)
    _port = port or options.port
    http.listen(_port)
    #http.start()
    # instance = IOLoop.instance()
    logging.info('- [%s is running on http://%s:%s]' % (app.__class__.__name__, host, _port))
    try:
        instance.start()
    except KeyboardInterrupt:
        instance.stop()

def show_urls(app):
    from torweb.urls import url_rules
    for urlspec in url_rules:
        #logging.info("%s %s %s" % (urlspec.regex.pattern, urlspec.handler_class, urlspec.kwargs))
        logging.info("%s <name:%s>" % (urlspec.regex.pattern, urlspec.name))

