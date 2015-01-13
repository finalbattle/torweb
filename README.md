# torweb

#### torweb is a second development based application framework tornado

1. **Install**

Example for virtualenv:

    $ cd ~
    $ mkdir env
    $ cd env
    $ virtualenv torweb
    $ ln -s ~/env/torweb/bin/python /usr/bin/python-torweb
    $ ln -s ~/env/torweb/bin/pip /usr/bin/pip-torweb
    $ pip-torweb install torweb
    $ ln -s ~/env/torweb/lib/python2.7/site-packages/torweb/start_app.py /usr/bin/torweb_startapp.py
    $ sudo chmod a+x /usr/bin/torweb_startapp.py


2. **Getting started**

Example for virtualenv torweb:
    
    Before start app of torweb, you'd have to install mysql, and set mysql root user and password.

And then, edit "**/usr/bin/torweb_startapp.py**" below to your username and password:

    MYSQL_ROOT_USER = "root"
    MYSQL_ROOT_PASS = "1"


Next, do follows to start you first application named torweb.

    $ cd ~
    $ mkdir projects
    $ cd projects
    $ torweb_startapp.py test
    $ cd test
    $ python-torweb dev_server.py
    [2013-10-25 10:53:18] * app server is running on http://0.0.0.0:8888
    [2013-10-25 10:53:18] * restart with reload

if you have got above tips, your first application has been built.
