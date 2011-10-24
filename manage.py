#!/usr/bin/env python
#coding=utf-8

from flask import Flask, current_app
from flaskext.script import Server, Shell, Manager, Command

from webapp import create_app
from webapp.extensions import db

manager = Manager(create_app('config.cfg'))

manager.add_command("runserver", Server('0.0.0.0',port=80))

def _make_context():
    return dict(db=db)
manager.add_command("shell", Shell(make_context=_make_context))

@manager.command
def createall():
    "Creates database tables"
    db.create_all()

@manager.command
def dropall():
    "Drops all database tables"
    
    if prompt_bool("Are you sure ? You will lose all your data !"):
        db.drop_all()

if __name__ == "__main__":
    manager.run()
