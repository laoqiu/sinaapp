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

from webapp.models import User, FinanceRecord


admin = Module(__name__)

@admin.route("/")
@admin_permission.require(404)
def index():
    return redirect(url_for('admin.cash_logs'))


@admin.route("/cash_logs")
@admin.route("/cash_logs/page/<int:page>")
@admin_permission.require(404)
def cash_logs(page=1):

    page_obj = FinanceRecord.query.filter(FinanceRecord.source==FinanceRecord.EXTRACT) \
                            .paginate(page, per_page=FinanceRecord.PER_PAGE)

    page_url = lambda page: url_for('admin.cash_logs', page=page)

    return render_template("admin/cash_logs.html", 
                            page_obj=page_obj,
                            paeg_url=page_url)


@admin.route("/cashed/<int:record_id>")
@admin_permission.require(404)
def cashed(record_id):
    
    record = FinanceRecord.query.get_or_404(record_id)

    record.status = FinanceRecord.SUCCESS
    db.session.commit()
    
    next_url = request.args.get('next','')
    if not next_url:
        next_url = url_for('admin.cash_logs')

    return redirect(next_url)
    



