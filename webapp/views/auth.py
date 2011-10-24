#! /usr/bin/env python
#coding=utf-8

import os
from datetime import datetime, timedelta

from flask import Module, Response, request, flash, json, g, current_app,\
    abort, redirect, url_for, session, render_template, send_file, send_from_directory

from flaskext.principal import identity_changed, Identity, AnonymousIdentity

from webapp.extensions import db, sina_api#, qq_api

from webapp.helpers import shorten

from webapp.models import User, UserMapper, UserProfile

from weibo import sina, qq

auth = Module(__name__)


@auth.route('/<source>/<app>/authorize')
def authorize(source, app):
    
    if source=='sina':
        try:
            key, token, callback = sina_api[app]
        except:
            abort(404)
        auth = sina.OAuthHandler(key, token, callback)
    
    #elif source=='qq':
    #    key, token, callback = qq_api
    #    auth = qq.OAuthHandler(key, token, callback)

    else:
        abort(404)

    authorize_url, request_token = auth.get_auth_url()
    session['oauth_token'] = str(request_token)
    
    return redirect(authorize_url)


@auth.route('/<source>/<app>/callback')
def callback(source, app):
    
    verifier = request.args.get('oauth_verifier','')
    #oauth_token = request.args.get('oauth_token','')

    if source=='sina':
        try:
            api_key, api_secret, callback = sina_api[app]
        except:
            abort(404)
        auth = sina.OAuthHandler(api_key, api_secret, callback)
        token_string = sina.oauth.OAuthToken.from_string(session['oauth_token'])
    
    #elif source=='qq':
    #    api_key, api_secret, callback = qq_api
    #    auth = qq.OAuthHandler(api_key, api_secret, callback)
    #    token_string = qq.oauth.OAuthToken.from_string(session['oauth_token']) 
    
    auth.set_req_token(token_string)
    token = auth.get_access_token(verifier)
    
    session['oauth_token'] = token.key
    session['oauth_token_secret'] = token.secret
    
    auth.setToken(token.key, token.secret)

    if source=='sina':
        username = auth.get_username()
    #elif source=='qq':
    #    username = auth.get_username()
    else:
        username = ''

    session['source'] = source
    session['app'] = app
    session['username'] = username

    if not g.user:
        mapper = UserMapper.query.filter(db.and_(UserMapper.source==source,
                                                 UserMapper.app==app,
                                                 UserMapper.access_token==token.key))\
                                 .first()
        if mapper:
            # login
            identity_changed.send(current_app._get_current_object(),
                                              identity=Identity(mapper.user.id))
        else:
            return redirect(url_for('auth.register'))

    g.user.bind(source, app, token.key, token.secret)

    # update profile
    update_profile(source, g.user, auth)

    return redirect(url_for('%s.index' % app))


@auth.route('/register')
def register():

    if g.user:
        return 'is logined'

    source = session.get('source')
    app = session.get('app')
    username = session.get('username')

    if source and username and app:
    
        token = session['oauth_token']
        secret = session['oauth_token_secret']

        if source=='sina':

            api_key, api_secret, callback = sina_api[app]
            auth = sina.OAuthHandler(api_key, api_secret, callback)
            auth.setToken(token, secret)
        
        #elif source=='qq':
        #    api_key, api_secret, callback = qq_api
        #    auth = qq.OAuthHandler(api_key, api_secret, callback)
        #    auth.setToken(token, secret)
        
        # 创建shorten
        while True:
            code = shorten(str(datetime.now()))
            if User.query.filter_by(shorten=code).count()==0:
                break

        email = '%s@openid.com' % code

        user = User(nickname=username,
                    email=email,
                    shorten=code)

        user.password = email

        user.profile = UserProfile()

        update_profile(source, user, auth)

        db.session.add(user)
        db.session.commit()

        # login
        identity_changed.send(current_app._get_current_object(),
                                          identity=Identity(user.id))

        user.bind(source, app, token, secret)

        return redirect(url_for('%s.post' % app))

    else:
        return redirect(url_for('frontend.login'))
    

def update_profile(source, user, auth):

    if source=='sina':
        api = sina.API(auth)

        username = auth.get_username()
        
        try:
            profile = api.get_user(screen_name=username)
        except:
            profile = None

        user.nickname = username
        user.profile.description = profile.description
        user.profile.image_url = profile.profile_image_url
        user.profile.gender = profile.gender
        user.profile.url = profile.url
        user.profile.followers_count = profile.followers_count
        user.profile.location = profile.location
        user.profile.verified = profile.verified
    
    #elif source=='qq':
    #    api = qq.API(auth)
    #    try:
    #        profile = api.user.info()
    #    except:
    #        profile = None

    return 



