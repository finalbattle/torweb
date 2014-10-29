# -*- coding: utf-8 -*-

import torweb
from setuptools import setup, find_packages

with open('README.txt') as file:
    #long_description = file.read()
    readlines = file.readlines()
    long_description = "".join(readlines)

print long_description
###
#install_requires=open('requirements.txt').readlines(),
###
setup(
    name = "torweb",
    version = torweb.__version__,
    packages = find_packages(),
    #packages = ["torweb"],
    include_package_data = True,
    author = "zhangpeng",
    author_email = "zhangpeng1@infohold.com.cn",
    url = "",
    description = "torweb",
    long_description=long_description,
    #install_requires=open('requirements.txt').readlines(),
    #install_requires=[
    #    "tornado", "PyYAML", "jinja2", "mysql-python", "storm", "sqlalchemy", "pymemcache"
    #],
)
