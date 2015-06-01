#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng1@infohold.com.cn>
"""
# yaml settings:

############################################
# LOGGER
############################################
version: 1
formatters:
  simpleFormater:
    #format: '%(asctime)s - %(levelname)s: %(message)s'
    format: '[%(name)s %(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  consoleFormatter:
    (): 'echo.logkit.ColoredConsoleFormatter'
  date_formatter:
    format: '[%(levelname)1.1s %(asctime)s %(process)s %(threadName)s  %(module)s:%(lineno)d] %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    formatter: consoleFormatter
    level: NOTSET
    stream: ext://sys.stdout
  file:
    class : torweb.logkit.iTimedRotatingFileHandler
    formatter: simpleFormater
    level: NOTSET
    filename: /usr/api-root/logs/echo-static/echo-static/log/info.log
    when: D
  iError:
    class : torweb.logkit.iTimedRotatingFileHandler
    formatter: date_formatter
    level: ERROR
    filename: /usr/api-root/logs/echo-static/echo-static/log/error.log
    when: D

loggers:
  logger:
    level: DEBUG
    #handlers: [console]
    handlers: 
      - console
  tornado:
    level: NOTSET
    qualname: tornado
    handlers: 
      - file
  iError:
    level: ERROR
    qualname: iError
    handlers: 
      - iError

root:
  level: INFO
  handlers: 
    - console
    - iError
    - file

myapp/__init__.py

import yaml
from logging.config import dictConfig

dictConfig(yaml.load(open(settings.yaml_path, 'r')))
itornado = logging.getLogger("console")
logger = logging.getLogger("file")
iError= logging.getLogger("iError")

"""

import time
import logging
from tornado.log import LogFormatter
from tornado.escape import _unicode
from tornado.util import basestring_type

class iFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'trace'):
            record.trace = '-'
        return super(iFormatter, self).format(record)

class iTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def shouldRollover(self, record):
        now = time.time()
        t = int(now)
        if t >= self.rolloverAt:
            return 1
        elif (now / self.interval) > (self.rolloverAt / self.interval):
            return 1
        # print "No need to rollover: %d, %d" % (t, self.rolloverAt)
        return 0

class iColoredConsoleFormatter(LogFormatter):
    colored_format = '[%(levelname)1.1s %(asctime)s] %(message)s'
    def format(self, record):
        if not hasattr(record, 'trace'):
            record.trace = '-'
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        assert isinstance(record.message, basestring_type)  # guaranteed by logging
        record.asctime = time.strftime(
            "%Y-%m-%d %H:%M:%S", self.converter(record.created))
        #prefix = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]' % \
        prefix = self.colored_format % \
            record.__dict__
        #if hasattr(self, "_color") and self._color:
        prefix = (self._colors.get(record.levelno, self._normal) +
                      prefix + self._normal)
        def safe_unicode(s):
            try:
                return _unicode(s)
            except UnicodeDecodeError:
                return repr(s)
        #message = (self._colors.get(record.levelno, self._normal) + record.message + self._normal)
        #formatted = prefix + " " + safe_unicode(message)
        formatted = prefix
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            # exc_text contains multiple lines.  We need to safe_unicode
            # each line separately so that non-utf8 bytes don't cause
            # all the newlines to turn into '\n'.
            lines = [formatted.rstrip()]
            lines.extend(safe_unicode(ln) for ln in record.exc_text.split('\n'))
            formatted = '\n'.join(lines)
        return formatted.replace("\n", "\n    ")
