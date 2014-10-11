#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

from torweb import script
from code import interact


class Command(object):
    def __init__(self, app):
        from torweb import make_application
        self.app = app
        self.application = application = make_application(app)
        self._actions = {
                'urls' :   urls(application),
        }
        for name, action in getattr(app, "actions", []):
            self._actions[name] = action(application)

    def run(self):
        script.run(self._actions, '')

    def register(self, func, name=None):
        name = name if name is not None else func.func_name
        self._actions[name] = func

def urls(app):
    def action():
        """show all urls"""
        for spec in app.url_handlers:
            print "%s\t\t\t%s(%s)"%(spec.regex.pattern, spec.handler_class, spec.kwargs)

    return action

