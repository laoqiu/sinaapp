#!/usr/bin/env python
#coding=utf-8
"""
    users.py
    ~~~~~~~~~~~~~
    :copyright: (c) 2011 by Laoqiu(laoqiu.com@gmail.com).
    :license: BSD, see LICENSE for more details.
"""

import hashlib

from datetime import datetime

from werkzeug import cached_property

from flask import abort, current_app

from flaskext.sqlalchemy import BaseQuery
from flaskext.principal import RoleNeed, UserNeed, Permission

#from types import DenormalizedText

from webapp.extensions import db

from webapp.permissions import moderator_permission, admin_permission


class UserQuery(BaseQuery):

    def from_identity(self, identity):
        """
        Loads user from flaskext.principal.Identity instance and
        assigns permissions from user.

        A "user" instance is monkeypatched to the identity instance.

        If no user found then None is returned.
        """

        try:
            user = self.get(int(identity.name))
        except ValueError:
            user = None

        if user:
            identity.provides.update(user.provides)

        identity.user = user

        return user
    
    def authenticate(self, login, password):        
        user = self.filter(db.or_(User.nickname==login,User.email==login))\
                   .filter(User.blocked==False).first()
        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False
        return user, authenticated   
     
    def search(self, key):
        query = self.filter(db.or_(User.email==key,
                                   User.nickname.ilike('%'+key+'%'),
                                   User.username.ilike('%'+key+'%'))) \
                    .filter(User.blocked==False)
        return query


class User(db.Model):

    __tablename__ = 'users'
    
    query_class = UserQuery
    
    MEMBER = 100
    MODERATOR = 200
    ADMIN = 300
    
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    alipay = db.Column(db.String(100))
    shorten = db.Column(db.String(6), unique=True)
    _password = db.Column("password", db.String(40), nullable=False)
    money = db.Column(db.Numeric(9,2), default=0.0) # 返利余额
    role = db.Column(db.Integer, default=MEMBER)
    receive_email = db.Column(db.Boolean, default=False)
    email_alerts = db.Column(db.Boolean, default=False)
    activation_key = db.Column(db.String(40))
    created_date = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime, default=datetime.now)
    blocked = db.Column(db.Boolean, default=False)
    
    profile = db.relation('UserProfile', backref='user', uselist=False)

    class Permissions(object):
        
        def __init__(self, obj):
            self.obj = obj
    
        @cached_property
        def send_message(self):
            if not self.receive_email:
                return null

            return admin_permission & moderator_permission
        
        @cached_property
        def edit(self):
            return Permission(UserNeed(self.obj.id)) & admin_permission
  
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

    def __str__(self):
        return u"%s" % self.nickname
    
    def __repr__(self):
        return "<%s>" % self
    
    @cached_property
    def permissions(self):
        return self.Permissions(self)
  
    def _get_password(self):
        return self._password
    
    def _set_password(self, password):
        self._password = hashlib.md5(password).hexdigest()
    
    password = db.synonym("_password", 
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self,password):
        if self.password is None:
            return False        
        return self.password == hashlib.md5(password).hexdigest()
    
    @cached_property
    def provides(self):
        needs = [RoleNeed('authenticated'),
                 UserNeed(self.id)]

        if self.is_moderator:
            needs.append(RoleNeed('moderator'))

        if self.is_admin:
            needs.append(RoleNeed('admin'))

        return needs
    
    @property
    def is_moderator(self):
        return self.role >= self.MODERATOR

    @property
    def is_admin(self):
        return self.role >= self.ADMIN


class UserProfile(db.Model):
    
    __tablename__ = 'user_profiles'

    PER_PAGE = 20
    
    user_id = db.Column(db.Integer, 
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        primary_key=True) 
    
    gender = db.Column(db.String(1), default='n') #n, m, f
    description = db.Column(db.String(100))
    image_url = db.Column(db.String(100))
    url = db.Column(db.String(100))
    followers_count = db.Column(db.Integer)
    verified = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(20))
    updatetime = db.Column(db.DateTime, default=datetime.now, 
                                        onupdate=datetime.now)
    
    def __init__(self, *args, **kwargs):
        super(UserProfile, self).__init__(*args, **kwargs)
    
    def __str__(self):
        return self.user_id
    
    def __repr__(self):
        return "<%s>" % self

    @property
    def get_city(self):
        r = self.city if self.city else self.province
        return r if r else ''


class UserMapper(db.Model):
    """ 微博用户授权信息
        source: sina, qq
        app: 我们下面将会有多个app
    """
    
    __tablename__ = "user_mappers"
    
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(255))
    access_secret = db.Column(db.String(255))
    source = db.Column(db.String(50))
    app = db.Column(db.String(10)) # taoke, 
    
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'))

    user = db.relation('User', backref='mappers')
    
    def __init__(self, *args, **kwargs):
        super(UserMapper, self).__init__(*args, **kwargs)

    def __str__(self):
        return u"%s - %s(%s)" % (self.user_id, self.app, self.source)
    
    def __repr__(self):
        return "<%s>" % self
    
    
def bind(self, source, app, token, secret):
    
    mapper = UserMapper.query.filter(db.and_(UserMapper.user_id==self.id,
                                             UserMapper.source==source,
                                             UserMapper.app==app)) \
                             .first()
    if mapper is None:
        mapper = UserMapper(user_id=self.id, 
                            source=source,
                            app=app)

    mapper.access_token = token
    mapper.access_secret = secret

    self.mappers.append(mapper)

    db.session.commit()


def unbind(self, source, app):
    mapper = UserMapper.query.filter(db.and_(UserMapper.user_id==self.id,
                                             UserMapper.source==source,
                                             UserMapper.app==app)).first()

    if mapper:
        db.session.delete(mapper)
        db.session.commit()


User.bind = bind
User.unbind = unbind

