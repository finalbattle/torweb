#!/usr/bin/env python
# -*- coding: utf-8 -*-
# created: zhangpeng <zhangpeng@ivtime.com>

#AUTHOR: yeshengzou # # gmail.com
#DATE: 2012.4.23
#LICENCE: GPLv3
  
import PIL
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from random import randint
from cStringIO import StringIO
from code import interact

#CHAR = 'acdefghijkmnpqrstuvwxyABCDEFGHJKLMNPQRSTUVWXY345789'
#LEN = len(CHAR) - 1
#PADDING = 20
#X_SPACE = 10 #两个字符之间最少相隔多少个像素
#TRY_COUNT = 30 #随机字符的位置尝试最多多少次,避免死循环
#WIDTH = 72
#HEIGHT = 26
#LINE_NUM = 2
##FONT = ImageFont.load('font.pil')
##FONT = ImageFont.load('/home/zhangpeng/share/fonts/arial.ttf')
##FONT = ImageFont.truetype('/home/zhangpeng/share/fonts/arial.ttf', 18)
#FONT = ImageFont.truetype('/home/zhangpeng/share/fonts/simsun.ttc', 30)

class Captcha(object):
    def __init__(self, CHAR='acdefghijkmnpqrstuvwxyABCDEFGHJKLMNPQRSTUVWXY345789',
                 PADDING=20, X_SPACE=10, TRY_COUNT=30, WIDTH=72, HEIGHT=26, LINE_NUM=2,
                 FONT='arial.ttf', FONT_SIZE=30,
                 BG_RGBA=(233, 248, 255), FL_RGBA=(48, 133, 18)):
        self.CHAR = CHAR
        self.LEN = len(CHAR) - 1
        self.PADDING = PADDING
        self.X_SPACE = X_SPACE
        self.TRY_COUNT = TRY_COUNT
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.LINE_NUM = LINE_NUM
        self.BG_RGBA = BG_RGBA
        self.FL_RGBA = FL_RGBA
        self.IMAGE_FONT = ImageFont.truetype(FONT, FONT_SIZE)
    def gen(self):
        CHAR = self.CHAR
        LEN = self.LEN
        PADDING = self.PADDING
        X_SPACE = self.X_SPACE
        TRY_COUNT = self.TRY_COUNT
        WIDTH = self.WIDTH
        HEIGHT = self.HEIGHT
        LINE_NUM = self.LINE_NUM
        FONT = self.IMAGE_FONT
        BG_RGBA = self.BG_RGBA
        FL_RGBA = self.FL_RGBA

        #im = Image.new('1', (WIDTH, HEIGHT), 'white')
        im = Image.new('RGBA', (WIDTH, HEIGHT), BG_RGBA)
        draw = ImageDraw.Draw(im)
        w, h = im.size
    
        #S = [(x, y, 'c')]
        S = []
        x_list = []
        y_list = []
        n = 0
        while True:
            n += 1
            if n > TRY_COUNT:
                break
            x = randint(0, w - PADDING)
            flag = True
            for i in x_list:
                if abs(x - i) < X_SPACE:
                    flag = False
                    continue
                if not flag:
                    break
            if not flag:
                continue
    
            y = randint(0, h - PADDING)
            x_list.append(x)
            y_list.append(y)
            S.append((x, y, CHAR[randint(0, LEN)]))
            if len(S) == 4:
                break
    
        for x, y, c in S:
            draw.text((x, y), c, fill=FL_RGBA, font=FONT)
    
        #加3根干扰线
        for i in range(LINE_NUM):
            x1 = randint(0, (w - PADDING) / 2)
            y1 = randint(0, (h- PADDING / 2))
            x2 = randint(0, w)
            y2 = randint((h - PADDING / 2), h)
            draw.line(((x1, y1), (x2, y2)), fill=FL_RGBA, width=1)
    
        S.sort(lambda x, y: 1 if x[0] > y[0] else -1)
        char = [x[2] for x in S]
        fileio = StringIO()
        im.save(fileio, 'gif')
        #im.save('img.gif', 'gif')
        im.show()
        return ''.join(char), fileio

if __name__ == '__main__':
    captcha = Captcha(FONT='/home/zhangpeng/share/fonts/simsun.ttc')
    print captcha.gen()
