#!/usr/bin/env python
#coding=utf-8

"""
    __init__.py
    ~~~~~~~~~~~~~

    :license: BSD, see LICENSE for more details.
"""
import os
import logging
import datetime

from logging.handlers import SMTPHandler, RotatingFileHandler

from flask import Flask, g, session, request, flash, redirect, json, url_for, render_template

from flaskext.principal import Principal, RoleNeed, UserNeed, identity_loaded
from flaskext.uploads import configure_uploads

from webapp import views, helpers
from webapp.extensions import db, mail, cache, photos

from webapp.models import User

DEFAULT_APP_NAME = 'webapp'

DEFAULT_MODULES = (
    (views.frontend, ""),
    (views.taoke, ""),
    (views.admin, "/admin"),
    (views.auth, "/auth"),
)

def create_app(config=None, modules=None):

    if modules is None:
        modules = DEFAULT_MODULES   
    
    app = Flask(DEFAULT_APP_NAME)
    
    # config
    app.config.from_pyfile(config)
    
    configure_extensions(app)
    
    configure_identity(app)
    configure_logging(app)
    configure_errorhandlers(app)
    configure_before_handlers(app)
    configure_template_filters(app)
    configure_context_processors(app)
    configure_uploads(app, (photos,))

    #configure_i18n(app)
    
    # register module
    configure_modules(app, modules) 

    return app


def configure_extensions(app):

    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app)


def configure_identity(app):

    principal = Principal(app)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        g.user = User.query.from_identity(identity)


def configure_context_processors(app):

    @app.context_processor
    def config():
        return dict(config=app.config)


def configure_template_filters(app):

    @app.template_filter()
    def timesince(value):
        return helpers.timesince(value)

    @app.template_filter()
    def format_date(date,s='full'):
        return helpers.format_date(date,s)

    @app.template_filter()
    def format_datetime(time,s='full'):
        return helpers.format_datetime(time,s)


def configure_before_handlers(app):

    @app.before_request
    def authenticate():
        g.user = getattr(g.identity, 'user', None)


def configure_errorhandlers(app):

    @app.errorhandler(401)
    def unauthorized(error):
        if request.is_xhr:
            return json.dumps({'error':"Login required"})
        flash("Please login to see this page", "error")
        return redirect(url_for("login", next=request.path))
  
    @app.errorhandler(403)
    def forbidden(error):
        if request.is_xhr:
            return jsonify({'error':'Sorry, page not allowed'})
        return render_template("errors/403.html", error=error)

    @app.errorhandler(404)
    def page_not_found(error):
        if request.is_xhr:
            return json.dumps({'error':'Sorry, page not found'})
        return render_template("errors/404.html", error=error)

    @app.errorhandler(500)
    def server_error(error):
        if request.is_xhr:
            return json.dumps({'error':'Sorry, an error has occurred'})
        return render_template("errors/500.html", error=error)


def configure_modules(app, modules):

    for module, url_prefix in modules:
        app.register_module(module, url_prefix=url_prefix)


def configure_logging(app):

    mail_handler = \
        SMTPHandler(app.config['MAIL_SERVER'],
                    app.config['DEFAULT_MAIL_SENDER'],
                    app.config['ADMINS'], 
                    'application error',
                    (
                        app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'],
                    ))

    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')

    debug_log = os.path.join(app.root_path, 
                             app.config['DEBUG_LOG'])

    debug_file_handler = \
        RotatingFileHandler(debug_log,
                            maxBytes=100000,
                            backupCount=10)

    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)
    app.logger.addHandler(debug_file_handler)

    error_log = os.path.join(app.root_path, 
                             app.config['ERROR_LOG'])

    error_file_handler = \
        RotatingFileHandler(error_log,
                            maxBytes=100000,
                            backupCount=10)

    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    app.logger.addHandler(error_file_handler)

