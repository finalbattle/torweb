#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import os
import re
import urlparse
import logging
from tornado.web import URLSpec
from code import interact

url_rules = []
class Url(object):
    def __init__(self, prefix="/", except_url=False, status_code=200):
        self.prefix = prefix
        self.handlers = []
        self.status_code = status_code

    def __call__(self, url, **kwds):
        def _(cls):
            kwname = kwds.get("name", None)
            prefix = kwds.get("prefix") or self.prefix
            status_code = self.status_code
            name = kwname or "%s.%s" % (cls.__module__, cls.__name__)
            if url == "/":
                _url = prefix
            else:
                #_url = prefix + "/" + re.sub("/{0,1}", "", url, 1)
                #_url = "/".join([prefix, re.sub("/{0,1}", "", url, 1)])
                if not prefix.endswith("/"):
                    prefix = prefix + "/"
                _url = urlparse.urljoin(prefix, re.sub("/{0,1}", "", url, 1))
            self.handlers.append(URLSpec(_url, cls, kwds, name=name))
            #logging.info("[status_code-->%s][url:%s]" % (status_code, _url))
            if status_code == 200:
                url_rules.append(URLSpec(_url, cls, kwds, name=name))
            setattr(cls, "url_pattern", _url)
            return cls
        return _
url = Url()
except_url = Url()
url404 = Url(status_code=404)
