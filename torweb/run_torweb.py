#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import tornado
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer
from datetime import datetime
from code import interact

def run(app, host='0.0.0.0', port=8888):
    if app._wsgi == True:
        container = WSGIContainer(app); http = HTTPServer(container)
    else:
        http = HTTPServer(app, xheaders=True)
    #http.bind(port, host)
    http.listen(port)
    #http.start()
    server_name = 'wsgi server' if app._wsgi else 'app server'
    instance = IOLoop.instance()
    print '[%s] * %s is running on http://%s:%s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), server_name, host, port)
    if app.settings['debug'] == True and app._wsgi == False:
        tornado.autoreload.start(instance)
        print '[%s] * restart with reload' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        instance.start()
    except KeyboardInterrupt:
        instance.stop()
