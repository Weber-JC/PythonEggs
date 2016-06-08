#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/3/18  WeiYanfeng
    封装操作队列的线程
"""

import sys

from threading import Thread
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

from weberFuncs import PrintTimeMsg,PrintAndSleep, GetCurrentTime

from CGlobalExitFlag import CGlobalExitFlag

class CQueueObject:
    def __init__(self,sQueueName):
        self.sQueueName = sQueueName
        self.queue = Queue() #(maxsize = 1000)      #处理队列，默认容量无限制

    def GetQueueName(self):
        return self.sQueueName
    def GetQueueSize(self):
        return self.queue.qsize()

    def PutToQueue(self, oObject):
        dictObj = {}
        dictObj['object'] = oObject
        dictObj['ins_time'] = GetCurrentTime()
        self.queue.put(dictObj, block=True)
        return self.queue.qsize()

    def GetFmQueue(self, sThreadName):
        while True:
            try:
                dictObj = self.queue.get(timeout=0.1) #timeout 0.1s
                self.queue.task_done()
                return dictObj
            except Empty: #如果 Queue 是空，就会出异常
                PrintAndSleep(0.1,'%s.GetFmQueue' % sThreadName,False) #避免过多日志
                return None

class CQueueThread(Thread):
    def __init__(self, gef, Q, cbDealFunc):
        self.gef = gef
        self.Q = Q
        self.cbDealFunc = cbDealFunc
        self.sQueueName = self.Q.GetQueueName()
        Thread.__init__(self, name = 'Thread'+self.sQueueName)
        self.setDaemon(True)

    def run(self): #Overwrite run() method, put what you want the thread do here
        iLoopCnt = 0
        while not self.gef.IsExitFlagTrue():
            iLoopCnt += 1
            try:
                dictObj = self.Q.GetFmQueue(self.getName())
                iQueueSize = self.Q.GetQueueSize()
                # if iQueueSize or dictObj:
                #     PrintTimeMsg("%s#%d.run.QueueSize=%s,dictObj=(%s)" % (
                #         self.getName(),iLoopCnt,iQueueSize,str(dictObj)))
                if self.cbDealFunc and dictObj:
                    self.cbDealFunc(self.sQueueName,dictObj)
                else:
                    if not self.cbDealFunc:
                        PrintTimeMsg("%s#%d.JustPrint.dictObj=(%s)" % (
                            self.getName(),iLoopCnt,str(dictObj)))
                #PrintAndSleep(5, "_doRun.Just4Debug")
            except Exception, e:
                PrintTimeMsg("CQueueThread.%s.Exception:%s" % (self.getName(),str(e)))
                raise
        PrintTimeMsg("CQueueThread.%s.END.gbSigExit=%s!" % (
                self.getName(),str(self.gef.IsExitFlagTrue())))

class CStartLoopThread(Thread):
    def __init__(self, gef, cbLoopRun):
        self.gef = gef
        self.cbLoopRun = cbLoopRun
        Thread.__init__(self, name = 'ThreadRead')
        self.setDaemon(True)

    def run(self): #Overwrite run() method, put what you want the thread do here
        iLoopCnt = 0
        while not self.gef.IsExitFlagTrue():
            iLoopCnt += 1
            try:
                if self.cbLoopRun:
                    self.cbLoopRun(iLoopCnt)
                else:
                    PrintAndSleep(1, "%s.Just4Debug" % (self.getName()))
            except Exception, e:
                PrintTimeMsg("CStartLoopThread.Exception:%s" % (str(e)))
                raise
        PrintTimeMsg("CStartLoopThread.END.gbSigExit=%s!" % (str(self.gef.IsExitFlagTrue())))

#--------------------------------------
def testThreadMain():
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

    gQueueSend = CQueueObject('Send')
    gQueueSend.PutToQueue(['Cmd0','Cmd1','Cmd2'])
    PrintAndSleep(1,'waitThread')
    threadSend = CQueueThread(gef,gQueueSend,None)
    threadSend.start()
    #threadDeal.join() #加上之后就不退出了
    PrintAndSleep(3,'testThreadMain')

#--------------------------------------
if __name__=='__main__':
    testThreadMain()