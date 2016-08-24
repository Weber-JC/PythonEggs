#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/8/5  WeiYanfeng
    基于串列表的命名管道（借助 socket 实现）客户端。

"""

import sys
import os
import socket
from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep,GetCurrentTimeMSs
from CSockReadWrite import CSockReadWrite

#--------------------------------------
class TCmdPipeClient:
    def __init__(self, sServerIPPort, sFileName4SE=''):
        # sFileName4SE = 全路径的文件名，用于对应服务端出现问题
        # WeiYF.20160805 sFileName4SE 默认取值为空串，表示无需输出
        self.sFileName4SE = sFileName4SE
        self.sServerIP = '127.0.0.1'
        self.iServerPort = 8888
        lsServer = sServerIPPort.split(':')
        if len(lsServer)>=2:
            if lsServer[0]: self.sServerIP = lsServer[0]
            self.iServerPort = int(lsServer[1])
        self.sServerIPPort = '%s:%s' % (self.sServerIP,self.iServerPort)
        self.sockRW = None

    def __del__(self):
        pass

    def ConnectToServer(self):
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientsocket.connect((self.sServerIP,self.iServerPort))
        self.sockRW = CSockReadWrite(self.clientsocket,'C')
        self.sockRW.bVerbosePrintCmdStr = False
        self.sockRW.SetObjIPPort(self.sServerIPPort)
        PrintTimeMsg("ConnectToServer(%s).pid=(%s)" % (self.sServerIPPort,os.getpid()))

    def CloseSocket(self):
        if self.sockRW:
            self.sockRW.sock.close()
        PrintTimeMsg("CloseSocket(%s).pid=(%s)" % (self.sServerIPPort,os.getpid()))
        self.sockRW = None

    def SendPipeRequest(self, CmdStr):
        try:
            if self.sockRW==None: self.ConnectToServer() #放到try内部，避免出异常
            dwCmdId = 1225 #WeiYF.20160805 固定取值
            bResult = self.sockRW.WriteCmdStrToLink(dwCmdId,CmdStr)
            if bResult: return bResult
        except Exception, e:
            import traceback
            traceback.print_exc()
            PrintTimeMsg('SendPipeRequest.Exception={%s}!' % (str(e)))
        self.CloseSocket()
        self.AppendToFile4SE('|'.join(CmdStr))
        return False

    def AppendToFile4SE(self, sMsg):
        if self.sFileName4SE=='': return
        with open(self.sFileName4SE,"a") as f: #追加模式输出
            sS = "[%s]%s\n" % (GetCurrentTimeMSs(),sMsg)
            f.write(sS)

def testTCmdPipeClient():
    c = TCmdPipeClient('127.0.0.1:8805')
    iCnt = 0
    while iCnt<5:
        bRet = c.SendPipeRequest(['Test','One','2','three','iCnt=%d' % iCnt])
        if not bRet:
            PrintTimeMsg("testTCmdPipeClient.SendPipeRequest.Error.iCnt=%d" % (iCnt))
            break
        PrintAndSleep(6,'testTCmdPipeClient.iCnt=%d!' % iCnt)
        iCnt += 1

#--------------------------------------
if __name__ == '__main__':
    testTCmdPipeClient()
