# -*- coding: utf-8 -*-

from torweb import get_version
#from setuptools import setup, find_packages
from distutils.core import setup

with open('README.md') as file:
    #long_description = file.read()
    readlines = file.readlines()
    long_description = "".join(readlines)

print long_description
###
#install_requires=open('requirements.txt').readlines(),
###
setup(
    name = "torweb",
    version = get_version(),
    packages = ["torweb",
                "torweb.lib",
                "torweb.lib.soaplib",
                "torweb.lib.soaplib.ext",
                "torweb.lib.soaplib.serializers",
                "torweb.lib.soaplib.util",
                "torweb.utils"],
    package_dir = {"torweb":"torweb"},
    package_data = {"torweb":["../*.txt", "../*.md"]},
    include_package_data = True,
    author = "zhangpeng",
    author_email = "zhangpeng1@infohold.com.cn",
    url = "https://github.com/finalbattle/torweb.git",
    description = "torweb",
    long_description=long_description,
    #install_requires=open('requirements.txt').readlines(),
    #install_requires=[
    #    "tornado", "PyYAML", "jinja2", "mysql-python", "storm", "sqlalchemy", "pymemcache"
    #],
)
