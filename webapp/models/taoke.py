#!/usr/bin/env python
#coding=utf-8
"""
    taoke.py
    ~~~~~~~~~~~~~
    :copyright: (c) 2011 by Laoqiu(laoqiu.com@gmail.com).
    :license: BSD, see LICENSE for more details.
"""

import hashlib

from datetime import datetime

from werkzeug import cached_property

from flask import abort, current_app

from flaskext.sqlalchemy import BaseQuery
#from flaskext.principal import RoleNeed, UserNeed, Permission

#from types import DenormalizedText

from webapp.extensions import db
from webapp.permissions import moderator_permission, admin_permission


class TaokeReport(db.Model):
    
    __tablename__ = "taoke_reports"
    
    PER_PAGE = 20
    
    id = db.Column(db.Integer, primary_key=True)
    outer_code = db.Column(db.String(12), index=True)   # 6位一个用户shorten
    trade_id = db.Column(db.String(20))
    num_iid = db.Column(db.String(50))
    item_title = db.Column(db.String(200))
    item_num = db.Column(db.Integer)
    shop_title = db.Column(db.String(50))
    seller_nick = db.Column(db.String(50))
    pay_time = db.Column(db.DateTime)
    pay_price = db.Column(db.Numeric(9,2))
    real_pay_fee = db.Column(db.Numeric(9,2))           # 实际支付金额
    commission = db.Column(db.Numeric(9,2))             # 用户获得拥金
    commission_rate = db.Column(db.String(10))          # 拥金比率
    
    __mapper_args__ = {'order_by': id.desc()}
    
    def __init__(self, *args, **kwargs):
        super(TaokeReport, self).__init__(*args, **kwargs)

    def __str__(self):
        return u"%s: %s" % (self.trand_id, self.item_title)

    def __repr__(self):
        return "<%s>" % self


class FinanceRecord(db.Model):
    
    __tablename__ = "finance_records"

    PER_PAGE = 20

    BUY = 100       # 购买
    COMM = 200      # 推荐成功
    EXTRACT = 300   # 提取

    WAIT = 100
    SUCCESS = 200
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Integer(3), nullable=False) #BUY, COMM, EXTRACT
    money = db.Column(db.Numeric(9,2)) # 支出(EXTRACT)为负数
    status = db.Column(db.Integer(3), default=WAIT) # WAIT, SUCCESS
    created_date = db.Column(db.DateTime, default=datetime.now)
    
    report_id = db.Column(db.Integer,
                          db.ForeignKey('taoke_reports.id', ondelete='CASCADE'))
    
    report = db.relation('TaokeReport', backref='finance_records')

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'))

    user = db.relation('User', backref='finance_records')

    def __init__(self, *args, **kwargs):
        super(FinanceRecord, self).__init__(*args, **kwargs)

    def __str__(self):
        return u"%s: %s" % (self.user_id, self.money)
    
    def __repr__(self):
        return "<%s>" % self
    
    @cached_property
    def name(self):
        data = {100: u"购买商品",
                200: u"推荐分成",
                300: u"提现"}
        return data.get(self.source, u'未知方式')
     
    @cached_property
    def get_status(self):
        data = {100: u"等待处理",
                200: u"成功"}
        return data.get(self.status, u'无状态')

