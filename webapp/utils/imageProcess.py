#! /usr/bin/env python
#coding=utf-8
"""
    imageProcess.py
    ~~~~~~~~~~~~~
    Recaptcha and Thumbnail

    :copyright: (c) 2010 by Laoqiu.
    :license: BSD, see LICENSE for more details.
"""

import sys, os, hashlib, datetime, random

import Image, ImageFont, ImageDraw, ImageEnhance

import StringIO

root_path = os.path.dirname(__file__)

def Recaptcha(text):
    img = Image.new('RGB',size=(110,26),color=(255,255,255))
    
    # set font
    font = ImageFont.truetype(os.path.join(os.path.dirname(__file__),'FacesAndCaps.ttf'),25)
    draw = ImageDraw.Draw(img)
    colors = [(250,125,30),(15,65,150),(210,30,90),(64,25,90),(10,120,40),(95,0,16)]
    
    # write text
    for i,s in enumerate(text):
        position = (i*25+4,0)
        draw.text(position, s, fill=random.choice(colors),font=font)
    
    # set border
    #draw.line([(0,0),(99,0),(99,29),(0,29),(0,0)], fill=(180,180,180))
    del draw
    
    # push data
    strIO = StringIO.StringIO()
    img.save(strIO,'PNG')
    strIO.seek(0)
    return strIO

def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

class Thumbnail(object):
    """
        t = Thumbnail(path)
        t.thumb(size=(100,100),outfile='file/to/name.xx',bg=False,watermark=None)
    """
    def __init__(self, path):
        self.path = path
        try:
            self.img = Image.open(self.path)
        except IOError:
            self.img = None
            print "%s not images" % path

    def thumb(self, size=(100,100), outfile=None, bg=False, watermark=None):
        """
            outfile: 'file/to/outfile.xxx'  
            crop: True|False
            watermark: 'file/to/watermark.xxx'
        """
        if not self.img:
            print 'must be have a image to process'
            return

        if not outfile:
            outfile = self.path

        #原图复制
        part = self.img
        part.thumbnail(size, Image.ANTIALIAS) # 按比例缩略
        
        size = size if bg else part.size # 如果没有白底则正常缩放
        w,h = size
        
        layer = Image.new('RGBA',size,(255,255,255)) # 白色底图

        # 计算粘贴的位置
        pw,ph = part.size
        left = (h-ph)/2
        upper = (w-pw)/2
        layer.paste(part,(upper,left)) # 粘贴原图

        # 如果有watermark参数则加水印
        if watermark:
            logo = Image.open(watermark)
            logo = reduce_opacity(logo, 0.3)
            # 粘贴到右下角
            lw,lh = logo.size
            position = (w-lw,h-lh)
            if layer.mode != 'RGBA':
                layer.convert('RGBA')
            mark = Image.new('RGBA', layer.size, (0,0,0,0))
            mark.paste(logo, position)
            layer = Image.composite(mark, layer, mark)

        layer.save(outfile, quality=100) # 保存
        return outfile
    
    def get_font(self, fontname, fontsize):
        return ImageFont.truetype(os.path.join(root_path, fontname), fontsize)

    def thumb_taoke(self, price, commission, outfile=None):
        """
            pic add price and commission
        """
        if not self.img:
            print 'must be have a image to process'
            return
        
        if not outfile:
            outfile = self.path

        #原图复制
        #layer = Image.new('RGBA', self.img.size, (255,255,255))
        layer = self.img
        w,h = self.img.size
        if layer.mode != 'RGBA':
            layer.convert('RGBA')
        
        # 创建字体
        price = u'%s' % price
        commission = u"%s" % commission
        unit = u"¥"
        label = u"返利"

        # 创建背景
        price_bg = Image.open(os.path.join(root_path, 'price_bg_big.png'))
        price_bg = reduce_opacity(price_bg, 0.8)
        p_w, p_h = price_bg.size
        
        comm_bg = Image.open(os.path.join(root_path, 'price_bg_small.png'))
        comm_bg = reduce_opacity(comm_bg, 0.7)
        c_w, c_h = comm_bg.size

        price_left = w - p_w - 10
        price_upper = h / 2 + 10
        comm_left = w - c_w - 10
        comm_upper = price_upper + p_h + 10

        # 粘贴
        mark = Image.new('RGBA', layer.size, (0,0,0,0))
        mark.paste(price_bg, (price_left, price_upper))
        mark.paste(comm_bg, (comm_left, comm_upper))
        layer = Image.composite(mark, layer, mark)
        
        # 写价格
        font_u_b = self.get_font('AndaleMono.ttf', 22)
        font_u_s = self.get_font('AndaleMono.ttf', 15)
        font_zh = self.get_font('yahei_mono.ttf',12)

        draw = ImageDraw.Draw(layer)

        # ¥
        draw.text((price_left+10, price_upper+4), unit, (255,255,255), font=font_u_b)
        
        # price
        space = 72
        fs = 22
        while True:
            font_temp = self.get_font('AndaleMono.ttf', fs)
            ft_w, ft_h = font_temp.getsize(price)
            if ft_w < space:
                break
            fs -= 1
        position = (price_left + 22 + (space - ft_w)/2, price_upper + (p_h - ft_h)/2)
        draw.text(position, price, (255,255,255), font=font_temp)
        
        # 返利
        draw.text((comm_left+8, comm_upper+4), label, (255,224,0), font=font_zh)

        # ¥
        draw.text((comm_left+38, comm_upper+4), unit, (255,224,0), font=font_u_s)
        
        # commission
        space = 48
        fs = 15
        while True:
            font_temp = self.get_font('AndaleMono.ttf', fs)
            ft_w, ft_h = font_temp.getsize(commission)
            if ft_w < space:
                break
            fs -= 1
        position = (comm_left + 45 + (space - ft_w)/2, comm_upper + (c_h - ft_h)/2)
        draw.text(position, commission, (255,224,0), font=font_temp)

        del draw
        layer.save(outfile, quality=100) # 保存
        return outfile

    

if __name__=='__main__':
    t = Thumbnail('pic.jpg')
    t.thumb_taoke(219.6, 18.6, 'pic1.jpg')
