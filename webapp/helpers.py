#!/usr/bin/env python
#coding=utf-8
"""
    helpers.py
    ~~~~~~~~~~~~~
    :license: BSD, see LICENSE for more details.
"""

import re
import markdown
import urlparse
import functools
import hashlib
import string

from datetime import datetime

from flask import current_app, g
from flaskext.babel import gettext, ngettext, format_date, format_datetime

from webapp.extensions import cache

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
    >>> o = storage(a=1)
    >>> o.a
    1
    >>> o['a']
    1
    >>> o.a = 2
    >>> o['a']
    2
    >>> del o.a
    >>> o.a
    Traceback (most recent call last):
    ...
    AttributeError: 'a'
    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'

storage = Storage

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug. From http://flask.pocoo.org/snippets/5/"""
    result = []
    for word in _punct_re.split(text.lower()):
        #word = word.encode('translit/long')
        if word:
            result.append(word)
    return unicode(delim.join(result))

markdown = functools.partial(markdown.markdown,
                             safe_mode='remove',
                             output_format="html")

cached = functools.partial(cache.cached,
                           unless= lambda: g.user is not None)

def request_wants_json(request):
    # we only accept json if the quality of json is greater than the
    # quality of text/html because text/html is preferred to support
    # browsers that accept on */*
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
       request.accept_mimetypes[best] > request.accept_mimetypes['text/html']

def timesince(dt, default=None):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """
    
    if default is None:
        default = gettext("just now")

    now = datetime.utcnow()
    diff = now - dt

    years = diff.days / 365
    months = diff.days / 30
    weeks = diff.days / 7
    days = diff.days
    hours = diff.seconds / 3600
    minutes = diff.seconds / 60
    seconds = diff.seconds 

    periods = (
        (years, ngettext("%(num)s year", "%(num)s years", num=years)),
        (months, ngettext("%(num)s month", "%(num)s months", num=months)),
        (weeks, ngettext("%(num)s week", "%(num)s weeks", num=weeks)),
        (days, ngettext("%(num)s day", "%(num)s days", num=days)),
        (hours, ngettext("%(num)s hour", "%(num)s hours", num=hours)),
        (minutes, ngettext("%(num)s minute", "%(num)s minutes", num=minutes)),
        (seconds, ngettext("%(num)s second", "%(num)s seconds", num=seconds)),
    )

    for period, trans in periods:
        if period:
            return gettext("%(period)s ago", period=trans)

    return default

def domain(url):
    """
    Returns the domain of a URL e.g. http://reddit.com/ > reddit.com
    """
    rv = urlparse.urlparse(url).netloc
    if rv.startswith("www."):
        rv = rv[4:]
    return rv

def shorten(origin):
    """ 加密转成短地址 """
    chars = list(string.letters + string.digits)
    hex = hashlib.md5(origin).hexdigest() 
  
    #把加密字符的16进制与0x3FFFFFFF进行位与运算  
    hexint = 0x3FFFFFFF & int("0x" + hex, 16)  
    outChars = ""
    for j in range(6):
        #把得到的值与0x0000003D进行位与运算，取得字符数组chars索引  
        index = 0x0000003D & hexint
        #把取得的字符相加  
        outChars += chars[index]
        #每次循环按位右移5位
        hexint = hexint >> 5
    
    return outChars


