#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/8/26  WeiYanfeng
    添加了线程缓存功能的管道服务端。
"""
import sys

from weberFuncs import PrintTimeMsg
from weberFuncs import CThreadCacheByQueue
from TCmdPipeServer import TCmdPipeServer

class TCmdPipeServerTCBQ(TCmdPipeServer):
    def __init__(self, iServerPort, sServerIP, ftCallBackForPush):
        self.ftCallBackForPush = ftCallBackForPush
        self.tcbq = CThreadCacheByQueue(self.ftCallBackForPush)
        TCmdPipeServer.__init__(self,iServerPort,sServerIP)

    def HandlePipeError(self, sRet, sMsg):
        PrintTimeMsg('TCmdPipeServerTCBQ.HandlePipeError(%s,%s)EXIT!' % (sRet,sMsg))
        self.SetLoopRunFlagToQuit('HandlePipeError=(%s.%s)' % (sRet,sMsg))
        sys.exit(-1)

    def HandlePipeRequest(self, CmdStr):
        self.tcbq.PutToQueue(CmdStr)
