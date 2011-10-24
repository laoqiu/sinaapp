#!/usr/bin/env python
#coding=utf-8

"""
    forms/tweets.py
    ~~~~~~~~~~~~~
    :license: BSD, see LICENSE for more details.
"""

from flask import g

from flaskext.wtf import Form, TextField, PasswordField, HiddenField, \
    BooleanField, RadioField, RecaptchaField, TextAreaField, SubmitField, \
    DateField, DateTimeField, FileField, SelectField, ValidationError,\
    required, email, equal_to, url, optional, regexp, length, validators

is_num = regexp(r'^\d{0,12}$', message=u"请填写数字")

class CashForm(Form):
    
    alipay = TextField(u"支付宝账户",validators=[
                required(message=u"请填写支付宝邮箱地址"), 
                email(message=u"邮箱格式错误")])

    money = TextField(u"提现金额", validators=[
                required(message=u"请填写您要提现的金额"),
                is_num])

    submit = SubmitField()
    
    hidden = HiddenField()

