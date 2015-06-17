#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

__version__ = "0.1.10"

def get_version():
    return __version__

import os
import re
from os.path import abspath, dirname, join
base_path = abspath(dirname(__file__))
import sys
sys.path.insert(0, abspath(join(base_path, 'utils')))
sys.path.insert(0, abspath(join(base_path, 'lib')))

#from torweb.application import make_application
