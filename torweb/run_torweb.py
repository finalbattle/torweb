#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import tornado
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer
from datetime import datetime
import logging
from code import interact
from tornado.options import define, options

define("cmd", default="runserver", metavar="runserver|urls")
define("port", default=8888)

tornado.options.parse_command_line()

def run(app, host='0.0.0.0', port=8888):
    if hasattr(app, "_wsgi") and app._wsgi == True:
        container = WSGIContainer(app); http = HTTPServer(container)
    else:
        http = HTTPServer(app, xheaders=True)
    #http.bind(port, host)
    port = options.port
    http.listen(port)
    #http.start()
    instance = IOLoop.instance()
    logging.info('- [%s is running on http://%s:%s]' % (app.__class__.__name__, host, port))
    if app.settings['debug'] == True and hasattr(app, "_wsgi") and app._wsgi == False:
        tornado.autoreload.start(instance)
        logging.info('- [%s restart with reload]' % (app.__class__.__name__))
    try:
        instance.start()
    except KeyboardInterrupt:
        instance.stop()

def show_urls(app):
    from torweb.urls import url_rules
    for urlspec in url_rules:
        #logging.info("%s %s %s" % (urlspec.regex.pattern, urlspec.handler_class, urlspec.kwargs))
        logging.info("%s <name:%s>" % (urlspec.regex.pattern, urlspec.name))

