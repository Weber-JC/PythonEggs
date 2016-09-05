#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/9/2  WeiYanfeng
    请简要说明当前程序的功能
"""
import sys
from CGlobalExitFlag import CGlobalExitFlag

import signal
gef = CGlobalExitFlag()
def SetGlobalFlagToQuit(errno):
    global gef
    gef.SetExitFlagTrue("SetGlobalFlagToQuit.errno=%d" % errno)
    sys.exit(errno)

def sig_handler(signum, frame):
    global gef
    gef.SetExitFlagTrue("receive a signal %d" % signum)

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)
#-------------------------------------------------
class CssException(Exception):
    def __init__(self, errno, errmsg):
        global gef
        self.errno = errno
        self.errmsg = errmsg
        gef.SetExitFlagTrue('CssException')

    def __str__(self):
        return 'CssException.errno=%s,errmsg=%s' % (repr(self.errno),repr(self.errmsg))