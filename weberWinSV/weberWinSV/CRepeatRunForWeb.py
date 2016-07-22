#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
    2016/7/19  WeiYanfeng
    在 BrokerIB/bottle/CRepeatRunForWeb.py 基础上改进而来,
    通过 检测pid状态 控制某个命令服务运行。

    设计说明，请参见 ../readme.md

    WeiYF.20160721 从属于 CWebSupervisor.py 暂不整理实现。
"""

import sys,os,time,json,errno
import psutil #subprocess

from weberFuncs import PrintTimeMsg,GetCurrentTime,PrintAndSleep,PrintInline,PrettyPrintStr


class CRepeatRunForWeb:
    """
        为WebServer进行运行封装
    """
    def __init__(self,sFNameConfig):
        self.sFNameConfig = sFNameConfig
        self._loadInitConfig(False)

        self.tmLastCheckRun = 0 #上次检查运行时间，避免被调用太频繁
        self.iCheckCount = 0 #检查计数

    def _loadInitConfig(self, bVerbose=True):
        self.dictConfig = {}
        with open(self.sFNameConfig,"r") as f:
            sData = f.read()
            # print "sData",sData
            # 这里configCmd.json要采用UTF-8编码，文件开头有UTF标记
            dictJson = json.loads(sData)
            for programId,dictParam in dictJson.items():
                if type(dictParam)==dict: #WeiYF.20150604是dict类型才执行
                    if not programId.startswith('<'):
                        self.dictConfig[programId] = LoadConfigByProgramId(self.sFNameConfig,programId,False)
        if bVerbose: PrintTimeMsg(PrettyPrintStr(self.dictConfig))
        self.dictCfgCmdOne = {}
        for programId,dictParam in self.dictConfig.items():
            rro = CRepeatRunOne(dictParam)
            self.dictCfgCmdOne[programId] = rro
        PrintTimeMsg("_loadInitConfig.Count=(%s)!" % (len(self.dictCfgCmdOne)))

    def ProgramCheckRun(self, bForce=False):
        secChkInterval = 30 #检查时间最小间隔，也是被监控进程退出
        if bForce or int(time.time())-self.tmLastCheckRun>=secChkInterval:
            iRunCnt = 0
            for programId,rro in self.dictCfgCmdOne.items():
                if rro.CheckAndRunOneCmd(False)!=0:
                    iRunCnt += 1
            self.tmLastCheckRun = int(time.time())
            if iRunCnt>0 and False:
                PrintTimeMsg("ProgramCheckRun.RunCnt=%s=" % (iRunCnt))
            return True
        self.iCheckCount += 1
        bVerbose = False #self.iCheckCount%10 == 0
        if bVerbose:
            PrintTimeMsg("ProgramCheckRun.ChkCnt=%s=" % (self.iCheckCount))
        return False

    def ProgramQueryAll(self, bVerbose=True):
        #查询所有程序运行状态
        dictRet = {}
        for programId,rro in self.dictCfgCmdOne.items():
            dictRet[programId] = rro.cco.GetStatusDict()
        if bVerbose: PrintTimeMsg("ProgramQueryAll="+PrettyPrintStr(self.dictConfig))
        return dictRet

    def ProgramStopOne(self,sProgramId):
        #停止某个程序
        rro = self.dictCfgCmdOne.get(sProgramId,None)
        if rro:
            rro.cco.CrtDelStopFile("CRT")
            bRet = rro.CheckAndRunOneCmd(False)
            PrintTimeMsg("ProgramStopOne(%s)=%s=" % (sProgramId,bRet))
            return bRet
        else:
            PrintTimeMsg("ProgramStopOne.get(%s)=Error" % (sProgramId))
            return False

    def ProgramStartOne(self,sProgramId):
        #启动某个程序
        rro = self.dictCfgCmdOne.get(sProgramId,None)
        if rro:
            rro.cco.CrtDelStopFile("DEL")
            bRet = rro.CheckAndRunOneCmd(False)
            PrintTimeMsg("ProgramStartOne(%s)=%s=" % (sProgramId,bRet))
            return bRet
        else:
            PrintTimeMsg("ProgramStartOne.get(%s)=Error" % (sProgramId))
            return False

    def ProgramRestartOne(self,sProgramId):
        #启动某个程序
        self.ProgramStopOne(sProgramId)
        self.ProgramStartOne(sProgramId)

    def ProgramGetLogTailTxt(self,sProgramId):
        rro = self.dictCfgCmdOne.get(sProgramId,None)
        if rro:
            return rro.cco.GetLogTailTxt()
        else:
            return "ProgramGetLogTailTxt(%s)=Error" % (sProgramId)


def LoopCRepeatRunMany(sFNameConfig="configCmd.json"):
    #WeiYF.20150610 该功能实现后，事实上就可以将
    rrfw = CRepeatRunForWeb(sFNameConfig)
    iCnt = 0
    while True:
        bRet = rrfw.ProgramCheckRun()
        # rrfw.ProgramRestartOne("TestHandleTradeFmRedis")
        # rrfw.ProgramQueryAll()
        #
        iCnt += 1
        bVerbose = iCnt%60 == 0
        PrintAndSleep(10,"*** LoopCRepeatRunMany.ProgramCheckRun(iCnt=%s)" % (iCnt),bVerbose)

######################################################
def stdinCRepeatRunOne():
    # c.LoopWaitCmdExec('ping juchecar.com -t')
    # c.LoopWaitCmdExec('ping juchecar.com -t')
    # c.LoopWaitCmdExec(['ping', 'juchecar.com','-t'])
    # c.LoopWaitCmdExec('ping www.juchecar.com')
    # c.LoopWaitCmdExec(r'C:\Python27\python.exe TcpChannelWin.py')
    #
    # dictP = {  'cmdExec': u'C:\\Python27\\python.exe .\\funcIB\\CTwsTransferMsgToRedis.py',
    #    'cmdTitle': u'\u8f6c\u9001\u884c\u60c5\u4fe1\u606f\u5230Redis',
    #    'endFlag': u'JustForEnd',
    #    'logProgramId': u'D:\\WeiYFGitSrc\\PythonProject\\BrokerIB\\log\\CTwsTransferMsgToRedis',
    #    'workDir': u'D:\\WeiYFGitSrc\\PythonProject\\BrokerIB\\'
    # }
    dictP = {  'cmdExec': u'ping juchecar.com',#  -t #dir C:\\
       'cmdTitle': u'\u8f6c\u9001\u884c\u60c5\u4fe1\u606f\u5230Redis',
       'endFlag': u'JustForEnd',
       'err2out': u'True',
       'ProgramId': u'CTwsTransferMsgToRedis',
       'logDir': u'D:\\WeiYFGitSrc\\PythonProject\\BrokerIB\\log\\',
       'workDir': u'D:\\WeiYFGitSrc\\PythonProject\\BrokerIB\\'
    }
    sJsonParam = sys.stdin.read()
    print "sJsonParam=",sJsonParam
    dictP = json.loads(sJsonParam)

    print "dictP=",PrettyPrintStr(dictP)
    StartCRepeatRunOne(dictP)
    return

def testPrintStdIn():
    """
        WeiYF.20150603
        虽然Popen可以通过 communicate 传递JSON数据串，但会因此阻塞而无法继续执行;
        虽然 StringIO 可以模拟将串转为 file object ，但这种对象无法在POpen环境下使用。
        http://stackoverflow.com/questions/20568107/python-stringio-for-popen
        http://stackoverflow.com/questions/163542/python-how-do-i-pass-a-string-into-subprocess-popen-using-the-stdin-argument
    """
    sJsonParam = sys.stdin.read()
    print "sJsonParam=",sJsonParam
    sys.exit(-1)

######################################################
if __name__ == '__main__':
    # testCConfigCmdOne()
    # testPrintStdIn()
    # stdinCRepeatRunOne()
    # mainCRepeatRunOne() #WeiYF.20150610 用于 runRepeatConfigBat.py程序调用，这种模式淘汰
    LoopCRepeatRunMany('configWeb.json')

