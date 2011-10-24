#! /usr/bin/env python
#coding=utf-8

import os
import time
from datetime import datetime, timedelta

from werkzeug import FileStorage

from flask import Module, Response, request, flash, json, g, current_app,\
    abort, redirect, url_for, session, render_template, send_file, send_from_directory

from flaskext.principal import identity_changed, Identity, AnonymousIdentity

from webapp.permissions import auth_permission, admin_permission 

from webapp.extensions import db, sina_api#, qq_api

from webapp.models import User, FinanceRecord
from webapp.forms import CashForm

from webapp.scripts.taobao_func import goods_from_url, taoke_items_convert, \
    get_taobao_item, get_taobao_shop, request as req

from webapp.utils.imageProcess import Thumbnail

from weibo import sina, qq

taoke = Module(__name__, subdomain='tuibei')


@taoke.route("/")
def index():
    
    next_url = session.get('next')
    if next_url:
        session.pop('next')
        return redirect(next_url)
    
    return render_template("taoke/index.html")


@taoke.route("/post")
@auth_permission.require(401)
def post():
    
    return render_template('taoke/post.html')


@taoke.route("/taobao", methods=('POST',))
@auth_permission.require(401)
def taobao():
    
    url = request.form.get('url','')

    item = goods_from_url(url)
    #print item

    if item:
        item['buyer_get'] = round(item.get('commission',0) * 0.5, 1)
        item['author_get'] = round(item.get('commission',0) * 0.2, 1)
        item['click_url'] = url_for('taoke.buy', 
                                    num_iid=item['num_iid'], 
                                    au=g.user.shorten, 
                                    _external=True)
        
        text_temp = u'现在购买<<<%(title)s>>> 只需要 %(price)s 元，还能得到 %(buyer_get)s 元返利，点击这里购买 >>>>>>>> '
        text = text_temp % item

        html_temp = u"""
            <div class="txt">
                <h3>%(title)s</h3>
                <p>价格: <span class="price">%(price)s</span> 元，购买返利: <span class="price">%(buyer_get)s</span> 元</p>
                <p>分享到微博，每个用户购买一件这个商品，您都将获取推荐返利: <strong class="price">%(author_get)s</strong> 元</p>
            </div>
            <div class="pic">
                <ul>
                    <li><img src="%(pic_url)s" alt="%(title)s" /></li>
                    <li><img src="%(pic_default)s" alt="%(title)s" /></li>
                </ul>
            </div>
            """
        
        item['pic_default'] = url_for('.static', filename='styles/taoke/images/bg-img.png')
        html = html_temp % item

        return json.dumps({'success':True,'html':html,'text':text,'item':item})

    return json.dumps({'error':u"没有找到商品,请检查url是否正确"})


@taoke.route("/buy/<int:num_iid>")
def buy(num_iid):
     
    items = taoke_items_convert([num_iid])
    #print items
    if items:
        item = items[0]

        item['click_url'] = url_for('taoke.click_url', 
                                    url=item['click_url'], 
                                    au=request.args.get('au',''),
                                    _external=True)

        item['score'] = item['seller_credit_score']
    else:
        item = get_taobao_item(num_iid)
        shop = get_taobao_shop(item['nick'])
        item['click_url'] = item['detail_url']
        item['score'] = shop['seller_credit']['level']
    
    return render_template("taoke/buy.html", item=item)


@taoke.route("/click")
@auth_permission.require(401)
def click_url():
    
    click_url = request.args.get('url','')
    author = request.args.get('au','')

    click_url += '%s%s' % (g.user.shorten, author)

    return redirect(click_url)


@taoke.route("/markpic", methods=('POST',))
@auth_permission.require(401)
def markpic():
    
    url = request.form.get('url')
    price = request.form.get('price', type=float)
    commission = request.form.get('commission', 0.0, type=float)

    if url and price:

        path, url = download_img(url)
        t = Thumbnail(path)
        w,h = t.img.size
        if w>420 or h>420:
            t.thumb(size=(420,420))
            time.sleep(0.1)
        t.thumb_taoke(price, commission)

        return json.dumps({'success':True,'pic':url})

    return json.dumps({'error':u'参数错误'})


def download_img(url):
    now = datetime.now()
    data = req(url)
    filename = now.strftime("%s") + '.jpg'
    folder =  now.strftime('upload/%Y/%m/%d')
    filedir = os.path.join(current_app.config['UPLOADS_DEFAULT_DEST'], folder)
    
    if not os.path.isdir(filedir):
        os.makedirs(filedir)

    filepath = os.path.join(filedir, filename)
    try:
        f = open(filepath, 'w')
        f.write(data)
        f.close()
    except:
        return None

    url = os.path.join(current_app.config['UPLOADS_DEFAULT_URL'], folder, filename)
    return filepath, url


@taoke.route("/finance")
@taoke.route("/finance/page/<int:page>")
@auth_permission.require(401)
def finance_records(page=1):

    page_obj = FinanceRecord.query.filter(User.id==g.user.id) \
                            .order_by(FinanceRecord.created_date.desc()) \
                            .paginate(page, per_page=FinanceRecord.PER_PAGE)

    page_url = lambda page: url_for('taoke.cash', page=page)
    
    return render_template('taoke/finance_records.html',
                            page_obj=page_obj,
                            page_url=page_url)


@taoke.route("/cash", methods=("GET","POST"))
@auth_permission.require(401)
def cash():
    
    form = CashForm(alipay=g.user.alipay)

    if form.validate_on_submit():

        money = request.form.get('money',0,type=int)
        print money

        if money > g.user.money:
            form.money.errors.append(u"对不起，可用金额不足提现金额")
        elif money<=0:
            form.money.errors.append(u"请输入正确的提现金额")
        else:
            money = -money
            record = FinanceRecord(money=money,
                                   user_id=g.user.id,
                                   source=FinanceRecord.EXTRACT,
                                   status=FinanceRecord.WAIT)
            db.session.add(record)
            g.user.money += money

            if g.user.alipay is None:
                g.user.alipay = form.alipay.data

            db.session.commit()
            return redirect(url_for('taoke.finance_records'))
            
    
    return render_template('taoke/cash.html', form=form)



@taoke.route('/login')
def login():
    
    session['next'] = request.args.get('next')

    return redirect(url_for('auth.authorize', source='sina', app='taoke'))
    

@taoke.route('/logout')
def logout():
    
    return redirect(url_for('frontend.logout'))


@taoke.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'taoke.ico', mimetype='image/vnd.microsoft.icon')


