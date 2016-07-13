# -*- coding:utf-8 -*-
"""
Created on 2016-5-30
@author: Weber Juche

TCmdStringSck 实现“串列表”传输协议客户端。
“串列表”打包解包采用串长度前置做法，即：
    将长度转为10进制逗号分隔串，采用分号分隔放在序列串头。后续依次是各个串内容。
从 TCmdSckA.py 简化而来，明文传输且开源，方便于内部扩展。
适用于“类似程序化交易等外围系统接入交易客户端”这样的场景；也方便于原型系统调试。

数据包头包括如下取值：
1.CmdId；4字节无符号整数。
2.序列化后包数据长度；4字节无符号整数。
其中，4字节无符号整数，采用16进制格式化输出，固定占位 8 字节；共8+8=16字节。
如果包头16字节，不符合16进制规则，则是非法数据，这样无需额外校验字节。

CmdId分段设计： 2^31=2147483648=0x80000000
2^31=心跳包，客户端和服务端都可以发送，收到后简单Echo应答，用于判断网络状态。
0=单向包，客户端和服务端都可以发送，收到后无需应答。服务端可以借此向客户端发送广播消息。客户端可以借此向服务端定时提交状态报告。
1~2^31-1 为客户端或服务端发起的原始命令请求标识；接收方收到并处理后，将该标识上添加 2^31 返回给发起方。递增，超上限后重新开始。

链接建立后，客户端首先向服务端发起“用户名/密码”校验请求，若不通过，服务端直接关闭该链接。
若校验通过，客户端与服务端保持该长链接。在长链接过程，客户端和服务端采用异步通讯模式，二者间可以随时通讯。

TCmdStringSck.py 通过多线程实现与服务端通讯。

"""
import sys
import socket
import struct

from weberFuncs import PrintTimeMsg,PrintAndSleep,printHexString,printCmdString,\
    GetCurrentTime#,GetTimeInteger,md5

#-------------------------------------------------
from CGlobalExitFlag import CGlobalExitFlag
from CQueueThread import CQueueObject,CQueueThread,CStartLoopThread

from mGlobalConst import CMD0_CHECK_AUTH,CMD0_ECHO_CMD
from cstpFuncs import CMDID_HREAT_BEAT,CMDID_NOTIFY_MSG,GenNewReqCmdId,IsHeartBeat,\
    IsCmdNotify, GetCmdType, GetCmdRequestFmReply,GetCmdReplyFmRequest

from mP2PLayoutConst import CMD0_P2PLAYOUT_SEND_SYSTEM_MSG,CMD0_P2PLAYOUT_SEND_CMD_TOPEER

from CSockReadWrite import CSockReadWrite

#-------------------------------------------------
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

class TCmdStringSck:
    """
        封装异步通讯 TCmdStringSck 基类。应用类从该类继承
    """
    def __init__(self, sHubId, sP2PKind, sServerIPAndPort, sAcctId, sAcctPwd, ynForceLogin, sClientInfo):
        global gef
        self.gef = gef
        self.sck = None

        self.sHubId = sHubId
        self.sP2PKind = sP2PKind

        self.iSecondsWaitForSynCmd = 60*60 # 主线程等待异步请求的秒数
        self.iSecondsReadFmServer = 10*60 # 从服务端读取数据的超时秒数

        (self.sServerIP, cSep, sServerPort) = sServerIPAndPort.partition(':')
        if cSep!=':':
            raise CssException(1,"TCmdStringSck.sServerIPAndPort=(%s)Error" % sServerIPAndPort)
        try:
            self.iServerPort = int(sServerPort)
        except ValueError:
            raise CssException(2,"TCmdStringSck.sServerPort=(%s)Error" % sServerPort)
        
        self.sAcctId = sAcctId
        self.sAcctPwd = sAcctPwd

        self.ynForceLogin = ynForceLogin
        self.sClientInfo = sClientInfo #将来再补充客户端信息

        self.cSep = '#' #内置命令字分隔符
        self.cLoginStatus = '@'    #//登录交互状态，取值: '@'=未连接; 'L'=登录中; 'R'=交互中;

        self.m_dictCmd = {} #已经发送的命令

        try:
            self.sck = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error,e:
            raise CssException(4,"socket.socket.There is sth wrong with your code:%s" % e)

        try:
            PrintTimeMsg("InitCmdSocket.connect(%s:%s)..." % (self.sServerIP,self.iServerPort))
            self.sck.connect((self.sServerIP,self.iServerPort))
        except socket.gaierror,e:
            raise CssException(5,"sck.connect.Address-related error connection to server:%s"%e)
        except socket.error,e:
            raise CssException(6,"sck.connect.Connection error:%s" % e)

        sServerIPPort = '%s:%s' % (self.sServerIP,self.iServerPort)
        self.oObj = CSockReadWrite(self.sck,'C')
        self.oObj.SetObjIPPort(sServerIPPort)

        self.QueueSend = CQueueObject('Send')
        self.QueueRecv = CQueueObject('Recv')
        lsThread = []
        # lsThread.append(CStartLoopThread(self.gef,self.cbForProcessLogic))
        lsThread.append(CStartLoopThread(self.gef,self.cbReadFmServerToQueue))
        lsThread.append(CQueueThread(self.gef,self.QueueRecv,self.cbDealQueueDataFmServer))
        lsThread.append(CQueueThread(self.gef,self.QueueSend,self.cbSendQueueDataToServer))
        for t in lsThread:
            t.start()
            #t.join() #加上之后就不退出了
        self.cLoginStatus = 'L' #进入登录状态
        self.SendReqCmd_ChkPasswd()

    def __del__(self):
        self.TerminateMainThread('QUIT')

    def TerminateMainThread(self, sHint):
        gef.SetExitFlagTrue(sHint)
        if hasattr(self,'oObj'):
            self.oObj.SetCloseQuitFlag(sHint)

    def StartMainThreadLoop(self):
        # 开始主线程循环
        try:  #以下是主线程；python 没有连接上的事件？那就直接调用
            iTryCnt = 0
            while not self.waitCheckIsConnected(1) and iTryCnt<30: #最多尝试3s
                PrintAndSleep(0.1,'Wait for ChkPasswd')
                iTryCnt += 1
            self.LoopAndProcessLogic() # 然后进入主线程循环，可以发送请求
            self.WaitForMainThreadQuit(self.iSecondsWaitForSynCmd)
        except CssException,e:
            import traceback
            traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
            PrintTimeMsg('TCmdStringSck.Exception.e=(%s)' % (str(e)))

    def WaitForMainThreadQuit(self, iTimeoutSeconds):
        # 等待主线程退出
        def cbWaitForAsynQuit(sHint,iWaitCount):
            # PrintTimeMsg('cbWaitForThread.%s#%d' % (sHint,iWaitCount))
            return []
        return self.gef.WaitAndCheck('WaitForMainThreadQuit',cbWaitForAsynQuit,iTimeoutSeconds)

    def cbReadFmServerToQueue(self, iLoopCnt): #called by StartOneThread.run()
        # 从服务端读取数据，转发到接收队列上
        sRet, oTuple = self.oObj.ReadCmdStrFromLink(self.iSecondsReadFmServer)
        if sRet=='OK':
            (dwCmdId,CmdStr) = oTuple
            if IsHeartBeat(dwCmdId):
                self.oObj.EchoHeartBeatMsg(CmdStr)
            else:
                dictObj = {}
                dictObj['CmdStr'] = CmdStr
                dictObj['dwCmdId'] = dwCmdId
                self.QueueRecv.PutToQueue(dictObj)
                iQueueSize = self.QueueRecv.GetQueueSize()
                # PrintTimeMsg('cbReadFmSocketToQueue.QueueSize=%s,dictObj=(%s)' % (
                #     iQueueSize,str(dictObj)))
        elif sRet=='TimeOut':
            self.oObj.SendHeartBeatMsg('0','HeartBeat TimeOut From Client')
        else:
            sErrMsg = oTuple
            self.TerminateMainThread("cbReadFmSocketToQueue.sErrMsg=(%s)" % (oTuple))#会退出

    def cbSendQueueDataToServer(self, sQueueName, dictObj):
        # 发送队列数据到服务端
        # PrintTimeMsg('cbSendQueueDataToServer.dictObj=%s=' % (str(dictObj)))
        dictParam = dictObj.get('object',{})
        CmdStr = dictParam.get('CmdStr',[])
        dwCmdId = dictParam.get('dwCmdId',CMDID_HREAT_BEAT)
        self.oObj.WriteCmdStrToLink(dwCmdId,CmdStr)

    def cbDealQueueDataFmServer(self, sQueueName, dictObj):
        # 处理从服务端返回的数据
        # PrintTimeMsg('cbDealQueueDataFmServer.dictObj=%s=' % (str(dictObj)))
        dictParam = dictObj.get('object',{})
        CmdStr = dictParam.get('CmdStr',[])
        dwCmdId = dictParam.get('dwCmdId',CMDID_HREAT_BEAT)
        sCmdType = GetCmdType(dwCmdId)
        if sCmdType=='Reply': #服务端的应答
            bDelCmd = True #是否删除请求命令。删除后表示该命令执行结束
            dwCmdId = GetCmdRequestFmReply(dwCmdId)
            sBakValue = self.m_dictCmd.get(dwCmdId,'')
            lsV = sBakValue.split(self.cSep)
            sCmd0 = '@sCmd0'
            sLogicParam = '@sLogicParam'
            if len(lsV)>=2:
                sCmd0 = lsV[0]
                sLogicParam = lsV[1]
            if self.cLoginStatus=='L' and sLogicParam==CMD0_CHECK_AUTH:
                self.handleCmdReply_ChkPasswd(CmdStr)
            else:
                bDelCmd =self.OnHandleReplyCallBack(sCmd0,sLogicParam,CmdStr,dwCmdId)
            if bDelCmd:
                try:
                    del self.m_dictCmd[dwCmdId]
                except KeyError,e:
                    PrintTimeMsg("cbDealQueueDataFmServer.del(%s).Except:%s" % (dwCmdId,e))
        elif sCmdType=='Notify': #服务端的通知
            self.OnHandleNotifyCallBack(CmdStr,dwCmdId)
        elif sCmdType=='Request': #服务端的请求
            lsRetCmdStr = self.OnHandleRequestCallBack(CmdStr,dwCmdId)
            dwRetCmdId = GetCmdReplyFmRequest(dwCmdId)
            self.__putCmdToQueue(lsRetCmdStr, dwRetCmdId)
        else: #心态包
            PrintTimeMsg("cbDealQueueDataFmServer.sCmdType＝(%s)Ignore!" % (sCmdType))

    def __putCmdToQueue(self, CmdStr, dwCmdId):
        # 发送请求命令
        if len(CmdStr)<1:
            raise CssException(7,'_putCmdToQueue.CmdStr=[]=Error!EXIT!')
        self.QueueSend.PutToQueue({
            'CmdStr': CmdStr,
            'dwCmdId': dwCmdId,
        })

    def SendNotifyMsg(self, CmdStr):
        # 发送通知消息
        self.__putCmdToQueue(CmdStr, CMDID_NOTIFY_MSG)

    def SendRequestCmd(self, CmdStr, sLogicParam=''):
        # 发送请求命令
        sCmd0 = CmdStr[0]
        if self.cSep in sCmd0: #不能有#
            raise CssException(8,'SendRequestCmd.sCmd0=[%s]Error!EXIT!' % sCmd0)
        sBakValue = str(sCmd0)+self.cSep+sLogicParam
        dwCmdId = GenNewReqCmdId()
        self.m_dictCmd[dwCmdId] = sBakValue #,ftCallBack
        self.__putCmdToQueue(CmdStr, dwCmdId)

    def SendReqCmd_ChkPasswd(self):
        # 发送登录请求命令
        CmdStr = (CMD0_CHECK_AUTH,self.sP2PKind,self.sHubId, self.sAcctId,self.sAcctPwd,self.ynForceLogin,self.sClientInfo)
        sLogicParam = CMD0_CHECK_AUTH
        self.SendRequestCmd(CmdStr, sLogicParam)

    def handleCmdReply_ChkPasswd(self,CmdStr):
        if len(CmdStr)<=0:
            raise CssException(12,'handleCmdReply_ChkPasswd.Error=%s!' % (CmdStr))
        if CmdStr[0][0]=='O': #string下标从0开始
            self.cLoginStatus = 'R'#进入交互状态
            if len(CmdStr)>=6:
                PrintTimeMsg('handleCmdReply_ChkPasswd(%s)OK,TimeNow=(%s)' % (CmdStr[3],CmdStr[4]))
        else:
            raise CssException(13,'handleCmdReply_ChkPasswd.Error=(%s)' % (','.join(CmdStr)))

    def waitCheckIsConnected(self, iTimeoutSeconds):
        # 等待检查是否连上服务端
        def cbCheckLoginOK(sHint,iWaitCount):
            # PrintTimeMsg('cbCheckLoginOK.%s#%d' % (sHint,iWaitCount))
            if self.cLoginStatus!='L':
                return ['OK','LoginOK']
            return []
        lsRet = self.gef.WaitAndCheck('waitCheckIsConnected',cbCheckLoginOK,iTimeoutSeconds)
        return (self.sck!=None) and (lsRet) and (lsRet[0][0]=='O')

    def LoopAndProcessLogic(self):
        # 供子类继承，用于处理客户端业务逻辑
        PrintTimeMsg("LoopAndProcessLogic...")

    def OnHandleReplyCallBack(self,sCmd0,sLogicParam,CmdStr,dwCmdId):
        # 供子类继承，用于接收并处理应答消息
        PrintTimeMsg("OnHandleReplyCallBack.sCmd0=%s,dwCmdId=%s,sLogicParam=%s,CmdStr=%s"
                    % (sCmd0, dwCmdId, sLogicParam, str(CmdStr)) )
        return True

    def OnHandleNotifyCallBack(self,CmdStr,dwCmdId):
        # 供子类继承，用于接收并处理通知消息
        PrintTimeMsg("OnHandleNotifyCallBack.dwCmdId=%s,CmdStr=%s" % (dwCmdId, str(CmdStr)) )

    def OnHandleRequestCallBack(self,CmdStr,dwCmdId):
        # 供子类继承，用于接收并处理请求消息
        PrintTimeMsg("OnHandleRequestCallBack.dwCmdId=%s,CmdStr=%s" % (dwCmdId, str(CmdStr)) )
        lsRetStr = ['OK']
        lsRetStr.extend(CmdStr)
        return lsRetStr

def TestTCmdStringSck():
    pass

#--------------------------------------
if __name__=='__main__':
    TestTCmdStringSck()
