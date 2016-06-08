#!/usr/local/bin/python
#-*- coding:utf-8 -*-

"""
Created on 2016-5-30
@author: Weber Juche

CSTP(Command String List Transfer Protocol) 命令串列表传出协议

借助 gevent 微线程实现CSTP异步接入框架 TCmdStringHub.py
设计目标：在支持传统“客户端/服务器(C/S)”架构前提下，扩展支持“客户端到客户端(P2P)”架构。
相关设计细节如下：
1.全程异步消息。并对消息进行分类：
    A.正向请求应答型。由客户端向服务端发起请求，服务端向客户端回送应答。
    B.反向请求应答型。由服务端向客户端发起请求，客户端向服务端回送应答。
    C.消息通知型。由客户端向服务端发起或者反向发起，但无需接收方回送应答。
    D.心跳包型。由客户端或服务端根据自身状况，间隔10分钟或1小时向对方发起；接收方收到后直接回送结果。
2.对请求应答型消息添加唯一标识，并通过多线程封装等实现同步。
3.心跳包参数设计，参见 CSockReadWrite.py
4.客户端连接上之后，需要首先向服务端发登录指令。这里需要说明如下：
    A.客户端账号串(sAcctIdStr)是在P2P架构中作为交互访问的唯一标识；
    B.相同账号的不同设备通过在sAcctIdStr添加后缀实现；
    C.客户端检查密码登录接口描述，参见 CHubCallbackBase.py

---------------------- 依赖包
pip install gevent

"""

import sys
import gevent
from gevent.queue import Queue
from gevent.server import StreamServer
# from gevent import monkey
# monkey.patch_all()  #WeiYF.20160322 暂时打上补丁

from weberFuncs import GetCurrentTime,PrintTimeMsg,\
    CAppendLogBase, ClassForAttachAttr

from CSockReadWrite import CSockReadWrite

from cstpFuncs import CMDID_HREAT_BEAT,GenNewReqCmdId,IsHeartBeat,IsCmdNotify,\
    GetCmdType, GetCmdRequestFmReply,GetCmdReplyFmRequest, CMD0_CHECK_PASSWD
#--------------------------------------
class TCmdStringHub(CAppendLogBase):
    def __init__(self, sHostName4Param, sServerIPPort, oHubCallback,
                 sLogFileName = __file__): #WeiYF.20160427 方便于应用程序调整日志位置
        CAppendLogBase.__init__(self,sLogFileName,'log')

        self.sHostName4Param = sHostName4Param
        self.oHubCallback = oHubCallback

        self.sServerIP = '127.0.0.1'
        self.iServerPort = 8888
        lsServer = sServerIPPort.split(':')
        if len(lsServer)>=2:
            if lsServer[0]: self.sServerIP = lsServer[0]
            self.iServerPort = int(lsServer[1])

        oBind = ClassForAttachAttr()
        oBind.sSNetHubIdStr = '%s:%s' % (self.sHostName4Param,self.iServerPort)
        oBind.sServerIPPort = '%s:%s' % (self.sServerIP,self.iServerPort)
        self.oHubCallback.HandleServerStart(oBind)

        # self.bTelnetTest = True
        self.bTelnetTest = False
        self.iSecondsTimeOut = 86400

        self.iMaxQueueReqNum = 5 #微线程请求队列消息积压数目
        self.fSecondsFlowCtrl = 0.0001 #流控休息秒数
        self.fSecondsToSwitch = 0.0000 #切换休息秒数
        self.fSecondsEchoCtrl = 0.0001 #应答控制休息秒数

        self.dictLinkQueue = {} #当前连接队列字典
        self.queueRequest = Queue() #当前请求队列

    def __del__(self):
        self.oHubCallback.HandleServerStop()

    def LoopAndWait(self):
        # PrintTimeMsg('LoopAndWait.To join, telnet %s %d' % (self.sServerIP, self.iServerPort))
        self.greenletRequest = gevent.spawn(self.cbLoopHandleQueueRequest)
        self.greenletRequest.start()
        self.greenletReply = gevent.spawn(self.cbLoopHandleQueueReply)
        self.greenletReply.start()

        s = StreamServer((self.sServerIP, self.iServerPort), self.__handleOneConnection)
        s.serve_forever()

    def cbLoopHandleQueueRequest(self):
        while True:
            sClientIPPort,dwCmdId,CmdStr = self.queueRequest.get()
            if IsCmdNotify(dwCmdId):
                self.oHubCallback.HandleNotifyMsg(sClientIPPort,CmdStr)
            else:
                self.oHubCallback.HandleRequestCmd(sClientIPPort,dwCmdId,CmdStr)
            # gevent.sleep(sleepSeconds)

    def cbLoopHandleQueueReply(self):
        while True:
            (sClientIPPort,dwCmdId,CmdOStr) = self.oHubCallback.HandleCheckReply()
            if sClientIPPort=='': #表示没有数据
                gevent.sleep(self.fSecondsEchoCtrl)
            else:
                if sClientIPPort=='*': #广播给所有链接
                    for v in self.dictLinkQueue.values():
                        v.put([dwCmdId,CmdOStr])
                else:
                    v = self.dictLinkQueue.get(sClientIPPort,None)
                    if v:
                        v.put([dwCmdId,CmdOStr])
                    else:
                        sMsg = 'sClientIPPort=%s,iCmdId=%s,CmdOStr=%s' % (sClientIPPort,dwCmdId,str(CmdOStr))
                        PrintTimeMsg("TransmitCmdReplyToQueue.IgnoreReply(%s)" % (sMsg))
                        self.WyfAppendToFile('HubIgnoreReply',sMsg)
                gevent.sleep(self.fSecondsToSwitch)

    def __handleOneConnection(self, sock, client_addr):
        sClientIPPort = '%s:%s' % (client_addr[0],client_addr[1])
        self.oHubCallback.HandleClientBegin(sClientIPPort)

        PrintTimeMsg("__handleOneConnection.sock=(%s)..." % str(sock))
        oObj = CSockReadWrite(sock,'S')
        oObj.SetObjIPPort(sClientIPPort)

        # self.BroadcastToClients('System','## joined from %s.' % (oObj.GetObjIPPort()))
        # self.WyfAppendToFile('GeventClient','%s.SNetClientJoin' % oObj.sClientIPPort)
        oObj.queueForWrite = Queue()
        self.dictLinkQueue[oObj.GetObjIPPort()] = oObj.queueForWrite
        try:
            r = gevent.spawn(self.__handleClientRead, oObj)
            w = gevent.spawn(self.__handleClientWrite, oObj)
            gevent.joinall([r, w]) #会阻塞在这里
            # PrintTimeMsg("__handleOneConnection.gevent.joinall END!")
        finally:
            #self.BroadcastToClients('System','## %s left the chat.' % oObj.GetObjIPPort())
            self.__hubQuitAndFreeLink(oObj,'__handleOneConnection')
        # self.oHubCallback.HandleClientEnd(sClientIPPort) # 会在 __hubQuitAndFreeLink 中调用

    def __handleClientRead(self, oObj):
        # 处理从链接上读取数据包
        while not oObj.bQuitLoopFlag:
            try:
                sRet, oTuple = oObj.ReadCmdStrFromLink(15) #(self.iSecondsTimeOut)
                if sRet=='OK':
                    (dwCmdId,CmdIStr) = oTuple
                    if IsHeartBeat(dwCmdId):
                        oObj.EchoHeartBeatMsg(CmdIStr)
                    else:
                        sCmdType = GetCmdType(dwCmdId)
                        if not self.DealSpecialCmdRequest(oObj,dwCmdId,CmdIStr):
                            if self.queueRequest.qsize()>self.iMaxQueueReqNum: #WeiYF.20160324 进行流控，消息积压则暂缓
                                gevent.sleep(self.fSecondsFlowCtrl) #0.0001
                            self.queueRequest.put([oObj.GetObjIPPort(),dwCmdId,CmdIStr])
                elif sRet=='TimeOut':
                    oObj.SendHeartBeatMsg('0','HeartBeat TimeOut From Server')
                else:
                    sErrMsg = oTuple
                    oObj.SetCloseQuitFlag("__handleClientRead.sErrMsg=(%s)" % (oTuple))#会退出
                # gevent.sleep(0)
            except Exception, e:
                import traceback
                traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
                PrintTimeMsg('__handleClientRead.Exception.e=(%s)' % (str(e)))
        self.__hubQuitAndFreeLink(oObj,'__handleClientRead.END')

    def __handleClientWrite(self, oObj):
        q = oObj.queueForWrite
        while (not oObj.bQuitLoopFlag) and q:
            dwCmdId,CmdOStr = q.get()
            oObj.WriteCmdStrToLink(dwCmdId,CmdOStr)
            gevent.sleep(self.fSecondsToSwitch)
        self.__hubQuitAndFreeLink(oObj,'__handleClientWrite.END')

    def __hubQuitAndFreeLink(self, oObj, sHint):
        if not oObj.bQuitLoopFlag:
            oObj.SetCloseQuitFlag(sHint)
            self.oHubCallback.SetCloseQuitFlag(sHint)
        if oObj.ChkFirstDoQuitEnd():
            sObjIPPort = oObj.GetObjIPPort()
            self.oHubCallback.HandleClientEnd(sObjIPPort)
            del(self.dictLinkQueue[sObjIPPort])
            PrintTimeMsg("__hubQuitAndFreeLink(%s)ForReason=%s" % (sObjIPPort,sHint))

    def DealSpecialCmdRequest(self,oObj,dwCmdId,CmdIStr):
        #转发命令请求
        # PrintTimeMsg('TransmitCmdRequest.CmdIStr=(%s)!' % str(CmdIStr))
        if CmdIStr[0]==CMD0_CHECK_PASSWD: # .startswith('ABLOGIN.ChkPasswd'):
            if oObj.cLoginStatus!='L':
                CmdOStr = ['ES', #系统错误
                           '99', #错误代码
                           'TransmitCmdRequest.Can not call (%s) after login!' % CmdIStr[0],
                           'TCmdStringHub.DealSpecialCmdRequest'] #WeiYF.20151223 返回ES，强制客户端重新登录
                oObj.WriteCmdStrToLink(GetCmdReplyFmRequest(dwCmdId),CmdOStr)
                oObj.SetCloseQuitFlag(sMsg)
                return True
            else:
                sClientIPPort = oObj.GetObjIPPort()
                (sClientIPPort,dwCmdId,CmdOStr) = self.oHubCallback.HandleCheckPasswd(sClientIPPort,dwCmdId,CmdIStr)
                oObj.WriteCmdStrToLink(dwCmdId,CmdOStr)
                # if CmdOStr[0][0]=='O':
                #     oObj.ChgLoginStatus()
                return True
        return False

def StartCmdStringHub(sHostName4Param, sServerIPPort, clsHubCallBack, tupleClsParam, sLogFileName):
    oHubCallback = clsHubCallBack(tupleClsParam)
    c = TCmdStringHub(sHostName4Param,sServerIPPort,oHubCallback, sLogFileName)
    c.LoopAndWait()

def mainCmdStringHub():
    from CHubCallbackBase import CHubCallbackBase
    from CHubCallbackQueue import CHubCallbackQueue
    sHostName4Param = 'LocalTest'
    sServerIPPort = '0.0.0.0:8888'
    sPythonDir = 'D:/WeiYFGitSrc/PythonProject/WxScanServ/ptSNetSck/'
    sDiffKeyTail = ''
    tupleClsParam = (sDiffKeyTail,)
    StartCmdStringHub(sHostName4Param,sServerIPPort,
                      # CHubCallbackBase,
                      CHubCallbackQueue,
                      tupleClsParam,sPythonDir+'runSNetHubRedis.py')

#--------------------------------------
if __name__ == '__main__':
    mainCmdStringHub()
