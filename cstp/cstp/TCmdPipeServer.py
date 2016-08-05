#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/8/5  WeiYanfeng
    基于串列表的命名管道（借助 socket 实现）服务端。

"""

import sys
import os
import socket
from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep
from CSockReadWrite import CSockReadWrite


#--------------------------------------
class TCmdPipeServer:
    def __init__(self, iServerPort, sServerIP='0.0.0.0'):
        self.sServerIP = sServerIP
        self.iServerPort = iServerPort
        self.sServerIPPort = '%s:%s' % (self.sServerIP,self.iServerPort)

        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind((self.sServerIP, self.iServerPort))
        self.serversocket.listen(5) #  become a server socket, maximum 5 connections
        # WeiYF.20160805 暂时保留5，看实际运行情况

        self.iSecondsTimeOut = 60 #3600 #86400 # 读取超时
        self.bLoopRunFlag = True  # 循环判断变量

        self.sockRW = None

        PrintTimeMsg('TCmdPipeServer(%s).pid=(%s)Start...' % (
            self.sServerIPPort, os.getpid()))
        self.LoopAndWaitPipe()

    def __del__(self):
        pass

    def LoopAndWaitPipe(self):
        iLoopCntAccept = 0
        while self.bLoopRunFlag:
            self.AcceptOneClient()
            iLoopCntRead = 0
            while self.bLoopRunFlag:
                try:
                    sRet,sMsg = self.sockRW.ReadCmdStrFromLink(self.iSecondsTimeOut)
                    if sRet=='OK':
                        (dwCmdId,CmdStr) = sMsg
                        self.HandlePipeRequest(CmdStr)
                    else:
                        PrintTimeMsg("LoopAndWaitPipe.Error=%s,%s!" % (sRet,sMsg))
                        break
                except Exception, e:
                    import traceback
                    traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
                iLoopCntRead += 1
            self.sockRW.sock.close()
            iLoopCntAccept += 1
            PrintAndSleep(10,"LoopAndWaitPipe.iLoopCntAccept=%s,iLoopCntRead=%s" % (
                iLoopCntAccept, iLoopCntRead))
        PrintTimeMsg("LoopAndWaitPipe.iLoopCntAccept=%s,QUIT!" % (iLoopCntAccept))

    def AcceptOneClient(self):
        connection, address = self.serversocket.accept()
        sClientIPPort = '%s:%s' % (address[0],address[1])
        PrintTimeMsg("AcceptOneClient.sClientIPPort=%s!" % (sClientIPPort))
        self.sockRW = CSockReadWrite(connection,'S')
        self.sockRW.SetObjIPPort(sClientIPPort)
        self.sockRW.cLoginStatus = 'R' #默认就是运行状态

    def HandlePipeRequest(self, CmdStr):
        pass

def mainCmdPipeServer():
    iServerPort = 8805
    sServerIP = '0.0.0.0'
    c = TCmdPipeServer(iServerPort, sServerIP)
    pass

#--------------------------------------
if __name__ == '__main__':
    mainCmdPipeServer()
