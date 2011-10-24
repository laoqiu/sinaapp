#!/usr/bin/env python
#coding=utf-8

"""
    taobaoapi.py
    ~~~~~~~~~~~~~

    Taobao API simple class
    
    :copyright: (c) 2011 by Laoqiu.
    :license: BSD, see LICENSE for more details.
"""

import hashlib, json
import re
import urllib, urllib2
from datetime import datetime
import time

from webapp.extensions import appkey, myappkey

class TaobaoAPI(object):
    """
    client = TaobaoAPI(appkey, appsecret)
    req = TaobaoRequest(method)
    req.setParams(fields,product_id)
    product = client.execute(req)
    """

    def __init__(self, appkey, appsecret, debug=False):
        self.key = appkey
        self.secret = appsecret
        if debug:
            self.apiurl = "http://gw.api.tbsandbox.com/router/rest"
        else:
            self.apiurl = "http://gw.api.taobao.com/router/rest"

    def _sign(self, params):
        src = self.secret + ''.join(["%s%s" % (k,v) for k,v in sorted(params.items())]) \
                          + self.secret
        return hashlib.md5(src).hexdigest().upper()
    
    def getParams(self, params):
        params['app_key'] = self.key
        params['v'] = '2.0'
        params['format'] = 'json'
        params['timestamp'] = datetime.now().strftime('%Y-%m-%d %X')
        params['sign_method'] = 'md5'
        params['sign'] = self._sign(params)
        return urllib.urlencode(params)
        
    def execute(self, request):
        try:
            params = self.getParams(request.params)
        except BadParamsError:
            return
        
        while True:
            source = urllib2.urlopen(self.apiurl, params).read()
            data = json.loads(source)
            if data.get('code',0)==7:
                time.sleep(10)
                print 'error 7: api get times overflow'
            else:
                break
        return data.values()[0]


class BadParamsError(Exception): pass


class TaobaoRequest(object):
    """
    make a request
    req = TaobaoRequest(method, fileds='num_iid,title,price', product_id=1)
    """

    def __init__(self, *args, **kwargs):
        self.params = {'method':args[0]}
        self.setParams(**kwargs)
    
    def setParams(self, *args, **kwargs):
        for key in kwargs.keys():
            self.params[key] = kwargs[key]


