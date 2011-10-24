#! /usr/bin/env python
#coding=utf-8

import os
import datetime

from werkzeug import FileStorage

from flask import Module, Response, request, flash, json, g, current_app,\
    abort, redirect, url_for, session, render_template, send_file, send_from_directory

from flaskext.principal import identity_changed, Identity, AnonymousIdentity

from webapp.permissions import auth_permission, admin_permission 

from webapp.extensions import db, sina_api#, qq_api

from webapp.models import User

from weibo import sina, qq

frontend = Module(__name__)


@frontend.route("/")
def index():
    return redirect(url_for('taoke.index', _external=True))


@frontend.route('/logout')
def logout():
    
    next_url = request.args.get('next','')
    session.pop('oauth_token')
    session.pop('oauth_token_secret')

    identity_changed.send(current_app._get_current_object(),
                              identity=AnonymousIdentity())  
    if not next_url:
        next_url = url_for('frontend.index')
    
    return redirect(next_url)


@frontend.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


