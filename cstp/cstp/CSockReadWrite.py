#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
Created on 2016-6-1
@author: Weber Juche

将 socket 读写过程进行建议封装。


心跳包指令接口描述如下：
[!HeartBeat.Request]
@=发起心跳包请求
#CmdStr[n]数据包:
1=sReasonCode             ;发送心跳包原因代码，默认是0=定时心跳
2=sReasonDesc             ;发送心跳包原因描述
3=iRequestCnt             ;心跳包发送计数
4=sYMDHnsSend             ;心跳包发送时间(YYYYMMDD-hhnnss)

[!HeartBeat.Reply]
@=心跳包回送应答,
#CmdStr[n]数据包，在保持原来CmdStr[1..n]基础上，追加 sYMDHnsEcho
5=sYMDHnsEcho             ;心跳包应答时间(YYYYMMDD-hhnnss)

"""
import sys
import socket

from weberFuncs import GetCurrentTime,PrintTimeMsg,printHexString,printCmdString
from CssException import CssException
from cstpFuncs import SerialCstpHeadFmString,SerialCmdStrFmString,SerialCstCmdStrToString,\
    CMDID_HREAT_BEAT, CMDID_NOTIFY_MSG, IsCmdRequest

class CSockReadWrite:
    """
        将Sock读写过程进行封装。
    """
    def __init__(self, sock, charCS):
        self.sock = sock            # 已经建立好的 socket 链接
        self.charCS = charCS        # 客户端、服务端角色，取值 C=客户端; S=服务端
        self.cLoginStatus = 'L'     # 登录交互状态，取值: 'L'=登录中; 'R'=交互中;
        self.bQuitLoopFlag = False  # 循环控制变量
        self.iQuitEndCnt = 0        # 用于控制链接断开后仅执行依次

        self.sObjIPPort = 'IP:Port' # 目标IP和端口号，

        self.iHeartBeatReqCnt = 0   # 心跳包请求计数

        self.bVerbosePrintCmdStr = True # 是否打印CmdStr数组
        pass

    def __del__(self):
        pass

    def SetObjIPPort(self, sObjIPPort):
        self.sObjIPPort = sObjIPPort # 目标IP和端口号

    def GetObjIPPort(self):
        return self.sObjIPPort

    def GetLoginStatus(self):
        return self.cLoginStatus

    def ChgLoginStatus(self):
        if self.cLoginStatus=='L': #登录输出后，转入运行状态
            self.cLoginStatus = 'R'

    def ChkFirstDoQuitEnd(self):
        self.iQuitEndCnt += 1
        if self.iQuitEndCnt == 1: #WeiYF.20160427 仅第1次执行End
            return True

    def SetCloseQuitFlag(self,sHint):
        PrintTimeMsg("SetCloseQuitFlag(%s)EXIT=%s!" % (self.sObjIPPort,sHint))
        self.bQuitLoopFlag = True
        self.sock.close()
        #gevent.sleep(0)

    def GetQuitLoopFlag(self):
        return self.bQuitLoopFlag

    def shouldReadLenData(self,iDataLen,iSecondsTimeOut=60*60):
        #从链接上读取指定长度的数据
        #  失败返回 ErrCode,sErrMsg
        #  成功返回 'OK',listOut
        sock = self.sock
        listOut = []
        while not self.bQuitLoopFlag:
            try:
                try:
                    sock.settimeout(iSecondsTimeOut)
                    datBuf = sock.recv(iDataLen-len(listOut))
                    sock.settimeout(None)
                    if datBuf:
                        listOut.extend(list(datBuf))
                    else:
                        return 'Error',"shouldReadLenData.Broken" #socket connection broken
                except socket.timeout:
                    return 'TimeOut',"shouldReadLenData.iSecondsTimeOut=%s=" % iSecondsTimeOut
            except socket.error,e:
                # raise CssException(401,'shouldReadLenData(%s)ErrOut=%s' % (iDataLen,str(e)))
                return 'Error','shouldReadLenData(%s)ErrOut=%s' % (iDataLen,str(e))
            if (len(listOut)>=iDataLen): break
        if listOut:
            return 'OK',listOut
        else:
            return 'Null',listOut

    def ReadCmdStrFromLink(self, iSecondsTimeOut):
        #从链接上读取CmdStr
        #  失败返回 ErrCode,sErrMsg
        #  成功返回 'OK',(dwCmdId,CmdStr)
        iTmSeconds = iSecondsTimeOut
        if self.charCS=='S' and self.cLoginStatus=='L':
            iTmSeconds = 5    #登录时，超时时间要短，避免链接攻击
        sRet,listHead = self.shouldReadLenData(16,iTmSeconds)
        if sRet!='OK':
            return sRet,'ReadCmdStrFromLink.Head(%s)' % (listHead)
        # printHexString("RcvDataFromClient.head",listHead)
        (dwCmdId,dwDataLen) = SerialCstpHeadFmString(''.join(listHead))
        if self.bVerbosePrintCmdStr:
            PrintTimeMsg('ReadCmdStrFromLink.dwCmdId=%d,dwDataLen=%d' % (dwCmdId,dwDataLen) )
        if self.charCS=='S' and self.cLoginStatus=='L':
            if not IsCmdRequest(dwCmdId):
                return 'Error','ReadCmdStrFromLink.Only receive RequestCmd in Login Stage!'
        sRet,listData = self.shouldReadLenData(dwDataLen,3)
        if sRet!='OK':
            return sRet,'ReadCmdStrFromLink.Data(%s)' % (listData)
        CmdStr = SerialCmdStrFmString(''.join(listData))
        if self.bVerbosePrintCmdStr:
            printCmdString("ReadCmdStrFromLink",CmdStr)
        return sRet,(dwCmdId,CmdStr)

    def WriteCmdStrToLink(self, dwCmdId, CmdStr):
        #将CmdStr输出到链接上
        if self.charCS=='S' and self.cLoginStatus=='L':
            if CmdStr[0][0]=='O': #登录成功后
                self.ChgLoginStatus()
        sData = SerialCstCmdStrToString(dwCmdId,CmdStr,self.bVerbosePrintCmdStr)
        try:
            self.sock.sendall(sData)
            return True
        except socket.error,e:
            self.SetCloseQuitFlag("Error sending data:%s!" % str(e))
            # raise CssException(402,"Error sending data:%s!" % str(e))
            return False

    def SendHeartBeatMsg(self, sReasonCode, sReasonDesc):
        #发送心跳包请求到链接上
        self.iHeartBeatReqCnt += 1
        CmdStr = ['!HeartBeat.Request',sReasonCode, sReasonDesc,
                  str(self.iHeartBeatReqCnt),GetCurrentTime()]
        self.WriteCmdStrToLink(CMDID_HREAT_BEAT,CmdStr)

    def EchoHeartBeatMsg(self, CmdIStr):
        #回送心跳包应答到链接上
        if CmdIStr[0]=='!HeartBeat.Request':
            CmdStr = CmdIStr[1:]
            CmdStr.append(GetCurrentTime())
            CmdStr.insert(0,'!HeartBeat.Reply')
            self.WriteCmdStrToLink(CMDID_HREAT_BEAT,CmdStr)
