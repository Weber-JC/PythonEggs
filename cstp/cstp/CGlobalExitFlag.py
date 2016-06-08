#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/3/18  WeiYanfeng
    封装线程全局等待标记
"""
import sys
from weberFuncs import PrintTimeMsg,PrintAndSleep

class CGlobalExitFlag:
    WAIT_SECONDS_SYN=0.01 #同步等待时长,秒

    def __init__(self):
        self.WAIT_SECONDS_NUM=int(1/self.WAIT_SECONDS_SYN) #1秒内的计数
        self.WAIT_SECONDS_LOG=60*self.WAIT_SECONDS_NUM #记录日志计数
        self.dictFlag = {} #通过字典避免global无效问题
        self.dictFlag["gbSigExit"] = False  #Ctrl+C退出信号

    def IsExitFlagTrue(self):
        return self.dictFlag["gbSigExit"]

    def SetExitFlagTrue(self,sMsg):
        self.dictFlag["gbSigExit"] = True
        PrintTimeMsg("%s,gbSigExit=%s"%(sMsg, self.dictFlag["gbSigExit"]))

    def WaitAndCheck(self, sHint, cbCheckFunc=None, iTimeoutSeconds=60):
        # 等待并调用某检查过程
        iWaitCount = 0
        while not self.IsExitFlagTrue():
            PrintAndSleep(self.WAIT_SECONDS_SYN,'WaitAndCheck.%s#%d' % (sHint,iWaitCount),
                          iWaitCount%self.WAIT_SECONDS_LOG==0)
            if cbCheckFunc:
                lsRet = cbCheckFunc(sHint,iWaitCount)
                if lsRet: return lsRet # cbFunc 返回非空列表，则直接返回对应值
            else:
                PrintTimeMsg('WaitAndCheck.JustPrint.%s#%d' % (sHint,iWaitCount))
            iWaitCount += 1
            if iWaitCount>self.WAIT_SECONDS_NUM*iTimeoutSeconds:
                return ['WTO','WaitAndCheck.TimeOut']
        return ['WSQ','WaitAndCheck.SigQuit']

#--------------------------------------
def testMain():
    pass
#--------------------------------------
if __name__=='__main__':
    testMain()