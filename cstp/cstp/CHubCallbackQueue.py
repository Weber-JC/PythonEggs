# -*- coding:utf-8 -*-
'''
Created on 2016-6-7
@author: Weber Juche

从 CHubCallbackBase 继承，借助 Queue 实现后台业务逻辑

'''
import gevent
from gevent.queue import Queue
from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep,ClassForAttachAttr
from cstpFuncs import CMDID_HREAT_BEAT,GetCmdReplyFmRequest

from CHubCallbackBase import CHubCallbackBase

#--------------------------------------
class CHubCallbackQueue(CHubCallbackBase):
    def __init__(self, sDiffKeyTail=''):
        CHubCallbackBase.__init__(self, sDiffKeyTail)
        self.queueForReturn = Queue() #当前请求队列

    def HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr):
        # 处理客户端请求命令
        self.oLink.iRequestCmdNum += 1
        PrintTimeMsg("HandleRequestCmd.%s.Fm(%s)=%s=" % (
            self.oBind.sSNetHubIdStr, sClientIPPort, ','.join(CmdIStr) ))
        if CmdIStr[0].startswith('LmtApi.EchoCmd'):
            CmdOStr = ['OK','Queue']
            CmdOStr.extend(CmdIStr)
            dwCmdId = GetCmdReplyFmRequest(dwCmdId)
            self.queueForReturn.put([sClientIPPort,dwCmdId,CmdOStr])
        return True

    def HandleCheckReply(self):
        # 检查返回给客户端的应答消息（包括通知消息）等
        PrintAndSleep(1,'HandleCheckReply')
        if not self.oLink:
            return ('',0,[])
        else:
            self.iTestReplyCnt += 1
            q = self.queueForReturn
            while not self.bQuitLoopFlag: #
                sClientIPPort,dwCmdId,CmdOStr = q.get()
                self.oLink.iReplyCmdNum += 1
                return (sClientIPPort,dwCmdId,CmdOStr)
                fSecondsToSwitch = 0.1
                gevent.sleep(fSecondsToSwitch)

#--------------------------------------
def testCHubCallbackQueue():
    bhc = CHubCallbackQueue() #oObj

if __name__=='__main__':
    testCHubCallbackQueue()