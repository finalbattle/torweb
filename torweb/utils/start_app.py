#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from os.path import abspath, dirname

############################################
MYSQL_ROOT_USER = "root"
MYSQL_ROOT_PASS = "1"
############################################

#start_path = abspath(dirname(__file__))
start_path = os.getcwd()
print "start_path:%s" % start_path


init_text = '''#!/usr/bin/python
# -*- coding: utf-8 -*-
# created by start_app

from os.path import abspath, dirname, join
base_path = abspath(dirname(__file__))

# 添加系统路径
import sys
sys.path.insert(0, abspath(join(base_path, '..', 'lib')))

from torweb.config import Yaml_Config
Yaml_Config(base_path, join(base_path, 'settings.yaml'))

metadata = sqlalchemy_config["%(app)s"]["metadata"]
session = sqlalchemy_config["%(app)s"]["session"]

'''

handler_text = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created by start_app

from torweb.handlers import BaseHandler
from %(app)s.shortcuts import *
from code import interact

class Handler(BaseHandler):
    def on_finish(self):
        from %(app)s import session
        session.remove()
        #print 'session removed'
    def render(self, template, **kwargs):
        tmpl = env.get_template(template)
        self.write(tmpl.render(**kwargs))
'''

shortcuts_text = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created by start_app

from torweb.urls import url
from torweb.handlers import *
from code import interact

from %(app)s import *

#cache.clear()

try:
    from storm.locals import *
    from storm.expr import Sum,LeftJoin,Eq,Or,And,Func
    from storm.tracer import debug as storm_debug
except:
    pass

from sqlalchemy import Table
from sqlalchemy.orm import mapper
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 设置模板目录
from torweb.tmpl import FragmentCacheExtension
debug = True
from jinja2 import Environment, PackageLoader, MemcachedBytecodeCache, FileSystemBytecodeCache
env = Environment(
    loader = PackageLoader('%(app)s', 'templates'),
    auto_reload = debug,
    extensions = [FragmentCacheExtension],
    bytecode_cache = MemcachedBytecodeCache(cache, prefix="%(app)s/jinja2/bytecode/", timeout=3600*24*8)
)
env.fragment_cache = cache
'''

settings_text = '''app: %(app)s
language: python

static_dir: static
static_url: /static/
static_domain: /static
#static_domain: http://static.%(app)s.com

schemes:
  - scheme: mysql
    alias: %(app)s
    user: %(MYSQL_ROOT_USER)s
    pass: %(MYSQL_ROOT_PASS)s
    host: 127.0.0.1
    port: 3306
    db: %(app)s
    charset: utf8
    storm: store
    sqlalchemy: session

memcached: ['127.0.0.1:11211']

############################################
# SessionStore
# MemcachedSessionStore
############################################
session_store: MemcachedSessionStore
'''

test_models_text = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created by start_app
from %(app)s.shortcuts import *
from torweb.db import CacheQuery

# sqlalchemy
test_model = Table('test_model', metadata, schema='%(app)s', autoload=True)
class Test_Model_Base(Base):
    __table__ = test_model
    __mapper_args__ = {
        'column_prefix':'_'
    }
    @classmethod
    def query(cls):
        return CacheQuery(cls)
    def get_name(self):
        return self._name
    def get_email(self):
        return self._email
    def __repr__(self):
        return u'<test_model '+self._name+'>'
    def __unicode__(self):
        return self.__repr__()

# storm
class Test_Model(Test_Model_Base):
    __storm_table__ = 'test_model'
    id = Int(primary=True)
    name = Unicode(default=u'')
    email = Unicode(default=u'')
'''

test_views_text = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created by start_app

from tornado.web import addslash
from torweb.urls import url
from torweb.handlers import BaseHandler
from %(app)s.handlers import Handler
from code import interact

@url(r'/')
class Index(Handler):
    def get(self):
        self.render('index.html')


@url(r'/test/')
class MyIndex(BaseHandler):
    def get(self, *args, **kwargs):
        self.write('application is running ...')
'''

dev_server_text = '''# -*- coding: utf-8 -*-

import %(app)s 
import tornado.web
import tornado.options
from torweb import run_torweb
from torweb import make_application 
from optparse import OptionParser
from code import interact


if __name__ == '__main__':
    debug = True
    usage = "usage: prog [options] arg1"
    default_port = 8888
    options = OptionParser(usage)
    options.add_option("-p", "--port", dest="port", default=default_port,
                       help="server listenning port, default is 8888",
                       metavar="PORT")
    (option, args) = options.parse_args()
    if debug:
        tornado.options.parse_command_line(args)
    app = make_application(%(app)s, debug, wsgi=False)
    run_torweb.run(app, port=option.port)
'''

command_text = '''# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

import %(app)s
from torweb.command import Command
from code import interact


if __name__ == '__main__':
    command = Command(%(app)s)
    command.run()
'''

test_sql_text = '''--
-- Table structure for table `user_info`
--

DROP TABLE IF EXISTS `user_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT '',
  `email` varchar(255) DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_info`
--

LOCK TABLES `user_info` WRITE;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;
UNLOCK TABLES;
'''

def start_app(app):
    app_path = os.path.join(start_path, app)
    app_init_file = os.path.join(start_path, app, '__init__.py')
    app_handlers_file = os.path.join(start_path, app, 'handlers.py')
    app_shortcuts_file = os.path.join(start_path, app, 'shortcuts.py')
    app_settings_file = os.path.join(start_path, app, 'settings.yaml')
    app_models_path = os.path.join(start_path, app, 'models')
    app_models_init_file = os.path.join(start_path, app, 'models', '__init__.py')
    app_models_test_file = os.path.join(start_path, app, 'models', 'test.py')
    app_views_path = os.path.join(start_path, app, 'views')
    app_views_init_file = os.path.join(start_path, app, 'views', '__init__.py')
    app_views_test_file = os.path.join(start_path, app, 'views', 'test.py')
    app_test_sql = os.path.join(start_path, app, 'models', 'test.sql')
    dev_server_file = os.path.join(start_path, "dev_server.py")
    command_file = os.path.join(start_path, "command.py")
    if not os.path.exists(app_path):os.makedirs(app_path)
    if not os.path.exists(app_init_file):
        with open(app_init_file, 'w') as file:
            file.write(init_text % {'app':app})
            file.close()
    if not os.path.exists(app_handlers_file):
        with open(app_handlers_file, 'w') as file:
            file.write(handler_text % {'app':app})
            file.close()
    if not os.path.exists(app_shortcuts_file):
        with open(app_shortcuts_file, 'w') as file:
            file.write(shortcuts_text % {'app':app})
            file.close()
    if not os.path.exists(app_settings_file):
        with open(app_settings_file, 'w') as file:
            file.write(settings_text % {'app':app, 'MYSQL_ROOT_USER':MYSQL_ROOT_USER, 'MYSQL_ROOT_PASS':MYSQL_ROOT_PASS})
            file.close()
    if not os.path.exists(app_models_path):os.makedirs(app_models_path)
    if not os.path.exists(app_models_init_file):
        with open(app_models_init_file, 'w') as file:
            file.write('')
            file.close()
    if not os.path.exists(app_models_test_file):
        with open(app_models_test_file, 'w') as file:
            file.write(test_models_text % {'app':app, 's':'s'})
            file.close()
    if not os.path.exists(app_views_path):os.makedirs(app_views_path)
    if not os.path.exists(app_views_init_file):
        with open(app_views_init_file, 'w') as file:
            file.write('')
            file.close()
    if not os.path.exists(app_views_test_file):
        with open(app_views_test_file, 'w') as file:
            file.write(test_views_text % {'app':app})
            file.close()
    if not os.path.exists(app_test_sql):
        with open(app_test_sql, 'w') as file:
            file.write(test_sql_text)
            file.close()
    if not os.path.exists(dev_server_file):
        with open(dev_server_file, 'w') as file:
            file.write(dev_server_text % {"app": app})
            file.close()
    if not os.path.exists(command_file):
        with open(command_file, 'w') as file:
            file.write(command_text % {"app": app})
            file.close()

import os
def start_db(app):
    cmd = "mysqladmin -u %(MYSQL_ROOT_USER)s -p%(MYSQL_ROOT_PASS)s create %(app)s" % {'app':app, 'MYSQL_ROOT_USER':MYSQL_ROOT_USER, 'MYSQL_ROOT_PASS':MYSQL_ROOT_PASS}
    os.system(cmd)
    load_cmd = "mysql -u %(MYSQL_ROOT_USER)s -p%(MYSQL_ROOT_PASS)s %(app)s < %(app)s/models/test.sql" % {'app':app, 'MYSQL_ROOT_USER':MYSQL_ROOT_USER, 'MYSQL_ROOT_PASS':MYSQL_ROOT_PASS}
    os.system(load_cmd)
if __name__ == '__main__':
    try:
        if sys.argv[1]:
            start_app(sys.argv[1])
            start_db(sys.argv[1])
            print sys.argv[1]
    except IndexError:
        print u'请输入app名字'
