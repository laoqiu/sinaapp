#!/usr/bin/env python
#coding=utf-8
"""
    models.py
    ~~~~~~~~~~~~~
    :license: BSD, see LICENSE for more details.
"""

import hashlib
from datetime import datetime
from mydb import SQLAlchemy, BaseQuery, DenormalizedText

db = SQLAlchemy('mysql://root@localhost/yoro_dev?charset=utf8')


class User(db.Model):

    __tablename__ = 'users'
    
    #query_class = UserQuery
    
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
    
    #profile = db.relation('UserProfile', backref='user', uselist=False)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

    def __str__(self):
        return u"%s" % self.nickname
    
    def __repr__(self):
        return "<%s>" % self
  
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
    commission_rate = db.Column(db.String(10))        # 拥金比率
    
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
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Integer(3), nullable=False) #BUY, COMM, EXTRACT
    money = db.Column(db.Numeric(9,2)) # 支出(EXTRACT)为负数
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
    

