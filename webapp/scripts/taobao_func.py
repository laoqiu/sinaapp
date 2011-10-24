#!/usr/bin/env python
#coding=utf-8

"""
    taobao_func.py
    ~~~~~~~~~~~~~
    :copyright: (c) 2011 by Laoqiu.
    :license: BSD, see LICENSE for more details.
"""

import urllib, urllib2
import re
import datetime, time
import hashlib
import json

from decimal import Decimal

from taobaoapi import myappkey, appkey, TaobaoAPI, TaobaoRequest
from models import db, User, TaokeReport, FinanceRecord

from gzipSupport import ContentEncodingProcessor

# gzip support
gzip_support = ContentEncodingProcessor

opener = urllib2.build_opener(gzip_support)
urllib2.install_opener(opener)


def get_headers(gzip=True):
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13",
        # "User-Agent": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13"
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language":"zh-cn,zh;q=0.5",
        # "Accept-Encoding":"gzip,deflate",
        "Accept-Charset":"GB2312,utf-8;q=0.7,*;q=0.7",
        "Keep-Alive":"115",
        "Connection":"keep-alive",
        # "Host":"",
        # "Referer":"",
    }
    if gzip:
        headers["Accept-Encoding"] = "gzip,deflate"
    return headers


def request(url, headers=None, data=dict()):
    if headers is None:
        headers = get_headers()
    
    data = urllib.urlencode(data) if data else None
    req = urllib2.Request(
            url = url,
            data = data,
            headers = headers
            )
    try:
        request = urllib2.urlopen(req)
        source = request.read()
        # print url
        # print request.code,request.msg
        request.close()
    except:
        source = None
        print "connect timeout"

    return source



##############################
#                            #
#     function for taobao    #
#                            #
##############################


def get_taobao_items(q):
    key, secret, nick = myappkey
    client = TaobaoAPI(key, secret)
    method = 'taobao.items.get'
    fields = 'num_iid,title,pic_url,price,nick,score,volume,location,post_fee,delist_time'
    q = q.encode('utf-8')
    order_by = 'price:asc'
    start_score = '8'

    req = TaobaoRequest(method,
                        fields=fields,
                        q=q,
                        order_by=order_by,
                        start_score=start_score,
                        page_size=200)

    source = client.execute(req)

    items = source.get('items',{'item':[]}).get('item',[])
    data = [{'title': g['title'],
             'nick': g['nick'],
             'pic_url': g['pic_url'],
             'num_iid': g['num_iid'],
             'detail_url': "http://item.taobao.com/item.htm?id=%s" % g['num_iid'],
             'price': float(g['price']),
             'volume': int(g['volume']),
             'score': int(g['score']),
             'post_fee': g['post_fee'],
             'delist_time': datetime.datetime.strptime(g['delist_time'],'%Y-%m-%d %H:%S:%M'),
             'location': g['location']['city'],
             'source': 'taobao'} for g in items]
    return data


def get_taobao_item(num_iid):
    
    key, secret, nick = myappkey
    client = TaobaoAPI(key, secret)
    method = 'taobao.item.get'
    fields = 'num_iid,detail_url,title,pic_url,price,nick,score,volume,location,post_fee,delist_time'

    req = TaobaoRequest(method, fields=fields, num_iid=num_iid)

    source = client.execute(req)
    print source

    item = source.get('item', None)

    return item


def get_taobao_taoke(q):
    key, secret, nick = myappkey
    client = TaobaoAPI(key, secret)
    method = 'taobao.taobaoke.items.get'
    fields = 'num_iid,title,price,nick,click_url,commission,commission_rate,commission_num,commission_volume,shop_click_url,seller_credit_score,item_location,volume'
    q = q.encode('utf-8')
    order_by = "price_asc"

    req = TaobaoRequest(method,
                        fields=fields,
                        keywords=q,
                        sort=order_by,
                        start_credit='3diamond',
                        page_size=200)

    source = client.execute(req)

    items = source.get('taobaoke_items',{'taobaoke_item':[]}).get('taobaoke_item',[])
    data = [{'title': g['title'],
             'nick': g['nick'],
             'num_iid': g['num_iid'],
             'detail_url': g['click_url'],
             'price': float(g['price']),
             'volume': int(g['volume']),
             'score': int(g['seller_credit_score']),
             'post_fee': None,
             'delist_time': None,
             'location': g['item_location'],
             'source': 'taobao'} for g in items]
    return data


def taoke_items_convert(num_iids):
    key, secret, nick = myappkey
    client = TaobaoAPI(key, secret)
    
    method = 'taobao.taobaoke.items.convert'
    fields = 'num_iid,title,nick,pic_url,price,click_url,commission,ommission_rate,commission_num,commission_volume,shop_click_url,seller_credit_score,item_location,volume'

    data = []
    # 每次转换最大输入40个num_iid
    n = len(num_iids)/40 + (len(num_iids) % 40 and 1 or 0)
    for i in range(n):
        ids = ','.join([str(i) for i in num_iids[i*40:(i+1)*40]])
        req = TaobaoRequest(method, 
                            fields=fields,
                            num_iids=ids,
                            nick=nick.encode('utf8'))
        
        source = client.execute(req)
        
        items = source.get('taobaoke_items',{'taobaoke_item':[]}).get('taobaoke_item',[])
        data.extend([{'num_iid': g['num_iid'],
                 'click_url': g['click_url'],
                 'pic_url': g['pic_url'],
                 'title': g['title'],
                 'nick': g['nick'],
                 'price': float(g['price']),
                 'commission': float(g['commission']),
                 'seller_credit_score': int(g['seller_credit_score']),
                 'source': 'taobao'} for g in items])

    return data


def get_taobao_shop(nick):
    
    key, secret, mynick = appkey
    #key, secret, mynick = myappkey
    client = TaobaoAPI(key, secret)
    
    method = 'taobao.user.get'
    fields = 'user_id,uid,nick,sex,buyer_credit,seller_credit,location'
    req = TaobaoRequest(method, fields=fields, nick=nick.encode('utf8'))

    source = client.execute(req)

    shop = source.get('user', None)

    return shop
    

def goods_from_url(url):
     
    re_ids = re.findall(r'id=(\d+)', url)
    
    num_iid = re_ids[0] if re_ids else None

    item = get_taobao_item(num_iid) if num_iid else None
    taoke_items = taoke_items_convert([num_iid])
    if taoke_items:
        item.update(taoke_items[0])

    return item


def order_from_taobao(date):

    key, secret, nick = myappkey
    
    client = TaobaoAPI(key, secret)
    method = 'taobao.taobaoke.report.get'
    fields = 'trade_id,num_iid,item_title,item_num,seller_nick,pay_price,pay_time,shop_title,commission,outer_code'

    page = 1
    items = []
    while page>0:
        req = TaobaoRequest(method,
                            fields=fields,
                            date=date.strftime('%Y%m%d'),
                            page_no=page,
                            page_size=40)

        source = client.execute(req)

        items.extend(source.get('taobaoke_report',{}).get('taobaoke_report_members',{}).get('taobaoke_report_member',[]))
        total = source.get('total_results',40)
        if total - page*40 > 0:
            page += 1
        else:
            page = -1

    if items:
        
        for r in items:
            trade_id = str(r['trade_id'])
            report = TaokeReport.query.filter_by(trade_id=trade_id).first()

            if report is None:
                report = TaokeReport(trade_id=trade_id)
                db.session.add(report)
                
                report.num_iid = r['num_iid']
                report.pay_time = datetime.datetime.strptime(r['pay_time'], '%Y-%m-%d %H:%S:%M')
                report.pay_price = r['pay_price']
                report.item_title = r['item_title']
                report.item_num = r['item_num']
                report.shop_title = r['shop_title']
                report.seller_nick = r['seller_nick']
                report.real_pay_fee = r['real_pay_fee']
                
                report.commission = Decimal(str(r['commission']))
                report.commission_rate = r['commission_rate']
                report.outer_code = r['outer_code']

                db.session.flush()
                
                # 给用户返利
                outer_code = r.get('outer_code','')
                shorten = [outer_code[:6], outer_code[6:]]

                for i,s in enumerate(shorten):
                    user = User.query.filter_by(shorten=s).first()

                    # 前面为购买者(50%)，后面为推荐者(20%返利)
                    rate = 0.5 if i==0 else 0.2

                    if user:
                        record = FinanceRecord()
                        record.money = Decimal(str(float(report.commission) * rate))
                        record.source = record.BUY if i==0 else record.COMM
                        record.report = report
                        record.user = user

                        user.money += record.money

                        db.session.add(record)

                db.session.commit()

    return items


