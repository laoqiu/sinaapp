#!/usr/bin/env python
#coding=utf-8

import threading
import urllib2
import datetime
from taobao_func import order_from_taobao

class RepeatableTimer(object):
    def __init__(self, interval, function, args=[], kwargs={}):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def start(self):
        self.stop()
        self._timer = threading.Timer(self.interval, self._run)
        self._timer.start()

    def restart(self):
        self.start()

    def stop(self):
        if self.__dict__.has_key("_timer"):
            self._timer.cancel()
            del self._timer
    def _run(self):
        try:
            self.function(*self.args, **self.kwargs)
        except:
            pass
        self.restart()

def getreport():
    now = datetime.datetime.now()
    prev = now + datetime.timedelta(days=-1)
    order_from_taobao(prev)
    print now


if __name__ == "__main__":
    print 'start timer........'
    a = RepeatableTimer(43200,getreport) # 12 hours one time
    a.start()
