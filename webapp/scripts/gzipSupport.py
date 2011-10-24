#!/usr/bin/env python
#coding=utf-8

"""
    yoryu member update
    ~~~~~~~~~~~~~

    :copyright: (c) 2010 by Laoqiu.
    :license: BSD, see LICENSE for more details.
"""

import urllib2
import zlib

from gzip import GzipFile
from StringIO import StringIO

class ContentEncodingProcessor(urllib2.BaseHandler):
    """A handler to add gzip capabilities to urllib2 requests """
 
    # add headers to requests
    def http_request(self, req):
        req.add_header("Accept-Encoding", "gzip, deflate")
        return req
 
    # decode
    def http_response(self, req, resp):
        old_resp = resp
        # gzip
        if resp.headers.get("content-encoding") == "gzip":
            gz = GzipFile(
                    fileobj=StringIO(resp.read()),
                    mode="r"
                    )
            resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        # deflate
        if resp.headers.get("content-encoding") == "deflate":
            gz = StringIO(deflate(resp.read()))
            resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code) 
            resp.msg = old_resp.msg
        return resp
 
# deflate support

def deflate(data): 
    try:
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except zlib.error:
        return zlib.decompress(data)
