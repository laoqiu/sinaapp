#!/usr/bin/env python
#coding=utf-8

from flaskext.mail import Mail
from flaskext.sqlalchemy import SQLAlchemy
from flaskext.cache import Cache
from flaskext.uploads import UploadSet, IMAGES

__all__ = ['mail', 'db', 'cache', 'photos']

mail = Mail()
db = SQLAlchemy()
cache = Cache()
photos = UploadSet('photos', IMAGES)

sina_api = {'taoke':('1899693215',
                     '4a72b1939c0f674257a618b8174e7dda',
                     'http://viimii.li/auth/sina/taoke/callback'),
            }

#qq_api = ('782500852',
#          '16b76b86be7f5975afbbbeb9a66a9cc3',
#          'http://localhost:8080/auth/qq/callback')


# appkey = (key, secret, nick)
appkey = ('12360***', '8cbafd956c0fb4a59b2127c3db87***', u"老秋")
          
myappkey = ('1235***', 'f07159fbf91f4585ea6b93a2bd40***', u"老秋")
          

