#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
    2016/8/25  WeiYanfeng
    封装处理对象队列的线程
"""
import sys
from threading import Thread
from WyfPublicFuncs import PrintTimeMsg,PrintAndSleep

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x
#----------------------------------------------------------
class CThreadDoSomething(Thread):
    """
        采用线程执行某函数，完成后线程退出
    """
    def __init__(self, ftCallBack):
        Thread.__init__(self, name = 'CThreadDoSomething')
        self.ftCallBack = ftCallBack
        self.setDaemon(True) # 加上setDaemon，子进程随父进程退出

    def run(self): # Overwrite run() method, put what you want the thread do here
        self.ftCallBack()
        PrintTimeMsg('CThreadDoSomething.End!')

def StartThreadDoSomething(ftCallBack):
    threadDeal = CThreadDoSomething(ftCallBack)
    threadDeal.start()

def testWyfThreadDoSth():
    def cbDoSth():
        PrintAndSleep(1,'cbDoSth')
    StartThreadDoSomething(cbDoSth)
    return
#----------------------------------------------------------
class CThreadCacheByQueue():
    def __init__(self, callBackDealOne):
        if not callBackDealOne:
            PrintTimeMsg('CThreadCacheByQueue.callBackDealOne=None,EXIT!')
            sys.exit(-1)
        self.callBackDealOne = callBackDealOne
        self.iDealCount = 0
        self.bLoopRunFlag = True
        self.queue = Queue()
        StartThreadDoSomething(self.ftCallBackForPush)

    def PutToQueue(self, oData): #oData是python对象，不限制类型
        self.queue.put(oData, block=True) #, False)
        return self.queue.qsize()

    def GetFmQueue(self):
        # WeiYF.20150512 从测试效果上看，Queue仅适合服务一个读线程
        # sCmdParam = self.queue.get(block=True) #block=True
        # WeiYF.20150409 Concurrent Queue.get() with timeouts eats CPU
        # 改为下面 get(timeout=1) 参数做法
        while self.bLoopRunFlag:
            try:
                oData = self.queue.get(timeout=0.1) #timeout 0.1s
                self.queue.task_done()
                return oData
            except Empty: #如果 Queue 是空，就会出异常
                import time
                sleepSeconds = 0.001 # 没有消息时，sleep
                time.sleep(sleepSeconds)

    def GetQueueSize(self):
        #return self.iSize
        return self.queue.qsize()

    def ftCallBackForPush(self):
        while self.bLoopRunFlag:
            self.callBackDealOne(self.GetFmQueue(), self.iDealCount)
            self.iDealCount += 1

    def SetLoopRunFlag(self, bFlag):
        self.bLoopRunFlag = bFlag
        PrintTimeMsg('CThreadCacheByQueue.SetLoopRunFlag=(%s)!' % (self.bLoopRunFlag))

def testWyfThreadQueue():
    def cbTest(oData,iDealCount):
        PrintTimeMsg('%d#cbTest.oData=%s=' % (iDealCount,oData))
    o = CThreadCacheByQueue(cbTest)
    iCnt = 0
    while iCnt<5:
        o.PutToQueue({'A':'abcd','B':1234})
        PrintAndSleep(1,'testWyfQueueThread.%d' %  iCnt)
        iCnt += 1

#-------------------------------
if __name__ == '__main__':
    # testWyfThreadDoSth()
    testWyfThreadQueue()

