# -*- coding:utf-8 -*-
'''
Created on 2016-6-7
@author: Weber Juche

从 CHubCallbackBase 继承，借助 Queue 实现后台业务逻辑

'''
import gevent
from gevent.queue import Queue
from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep,ClassForAttachAttr
from cstpFuncs import CMD0_ECHO_CMD,GetCmdReplyFmRequest

from CHubCallbackBasicBase import CHubCallbackBasicBase

#--------------------------------------
class CHubCallbackQueueBase(CHubCallbackBasicBase):
    def __init__(self,sHubId):
        CHubCallbackBasicBase.__init__(self,sHubId)
        self.__queue4Return = Queue() #当前应答队列

    def PutCmdStrToReturnQueue(self, lsCmdStr):
        self.__queue4Return.put(lsCmdStr)

    def GetCmdStrFmReturnQueue(self):
        return self.__queue4Return.get() # (sClientIPPort,dwCmdId,CmdOStr)

    def HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr):
        # 处理客户端请求命令
        bDone = CHubCallbackBasicBase.HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr)
        if not bDone and CmdIStr[0].startswith(CMD0_ECHO_CMD):
            CmdOStr = ['OK','CHubCallbackQueueBase']
            CmdOStr.extend(CmdIStr)
            dwCmdId = GetCmdReplyFmRequest(dwCmdId)
            self.PutCmdStrToReturnQueue([sClientIPPort,dwCmdId,CmdOStr])
            bDone = True
        return bDone

    def DoHandleCheckAllLinkReply(self):
        # 处理检查所有链接的应答返还消息（包括通知消息）等
        # 该函数在该类中实现后，一般情况下子类无需再继承。
        while not self.bQuitLoopFlag:
            return self.GetCmdStrFmReturnQueue()

#--------------------------------------
def testCHubCallbackQueueBase():
    bhc = CHubCallbackQueueBase('sHubId') #oObj

if __name__=='__main__':
    testCHubCallbackQueueBase()