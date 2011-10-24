#!/usr/bin/env python
from webapp import create_app

app = create_app('config.cfg')

from flup.server.fcgi import WSGIServer
WSGIServer(app,bindAddress='/tmp/webapp.sock').run()
