#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import os
import re
from tornado.web import URLSpec
from code import interact

class Url(object):
    def __init__(self, prefix="/"):
        self.prefix = prefix
        self.handlers = []

    def __call__(self, url, **kwds):
        def _(cls):
            kwname = kwds.get("name", None)
            prefix = kwds.get("prefix") or self.prefix
            name = kwname or "%s.%s" % (cls.__module__, cls.__name__)
            if url == "/":
                _url = prefix
            else:
                _url = os.path.join(prefix, re.sub("/{0,1}", "", url, 1))
            self.handlers.append(URLSpec(_url, cls, kwds, name=name))
            setattr(cls, "url_pattern", _url)
            return cls
        return _
url = Url()
except_url = Url()
