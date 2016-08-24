#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
2016/7/21  WeiYanfeng

依据参数配置，分组启动并控制其它 cmdProgram=命令行程序 运行的工具。
参数配置说明请参见 demoSettingsWinSV.py 单元。

这些 cmdProgram 具有如下特征：
1. 一般作为服务程序运行。
2. 没有图形界面。
3. 有标准输出和标准错误输出，但没有标准输入。

CWinSupervisor 的控制运行单个 cmdProgram 的逻辑如下：
1. 若 stopFile 存在，则直接控制相应程序退出。
2. 若 pidFile 存在，则检查其对应的pid是否存在，若存在，则继续检测该服务。
3. 进入到 workDir，启动相应命令，并
    A.将其输出重定向到 outFile 和 errFile 中。
    B.将其pid记录到 pidFile 中。
    C.将启动服务日志追加方式记录到 workDir下的 logWeberWinSV.txt 中
4.循环1分钟：
    A.检测对应进程状态，并更新 pidFile 的时间，以表明对应命令正常运行。
    B.检测 stopFile 是否存在，若存在，则终止对应进程运行。
"""

import sys
import os

from weberFuncs import PrintTimeMsg,GetCurrentTime,PrintAndSleep
from winsvFuncs import LoadWinSVConfigFmFile
from CWinSVProgram import CWinSVProgram
#-------------------------------------------------
class CWinSupervisor:
    def __init__(self, srcfile, sPythonFileName, sDictVarName, sLongIdStr):
        PrintTimeMsg("CWinSupervisor.__init__.srcfile=%s=" % srcfile)
        PrintTimeMsg("CWinSupervisor.__init__.sPythonFileName=%s=" % sPythonFileName)
        PrintTimeMsg("CWinSupervisor.__init__.sDictVarName=%s=" % sDictVarName)
        PrintTimeMsg("CWinSupervisor.__init__.sLongIdStr=%s=" % sLongIdStr)
        self.sStartCWD = os.getcwd()
        PrintTimeMsg("CWinSupervisor.__init__.sStartCWD=%s=" % self.sStartCWD)
        self.lsProgram = LoadWinSVConfigFmFile(srcfile,sPythonFileName, sDictVarName, sLongIdStr)
        iProgramCnt = len(self.lsProgram)
        if iProgramCnt==0:
            PrintTimeMsg("CWinSupervisor.__init__.iProgramCnt=(%d)Error EXIT!" % iProgramCnt)
            sys.exit(-1)
        PrintTimeMsg("CWinSupervisor.__init__.iProgramCnt=(%d)!" % iProgramCnt)

        self.iCheckIntervalSeconds = 60

        self.lsWinSV = []
        for dictParam in self.lsProgram:
            oWinSV = CWinSVProgram(dictParam)
            self.lsWinSV.append(oWinSV)

    def __del__(self):
        pass

    def LoopAndWatchPrograms(self):
        iLoopCnt = 0
        while True:
            os.chdir(self.sStartCWD) #回到启动时的目录
            iLoopCnt += 1
            iStart,iStop = 0,0
            for oWinSV in self.lsWinSV:
                iChg = oWinSV.CheckAndRunOneCmd()
                if iChg>0: iStart += 1
                if iChg<0: iStop += 1
            if iStart>0 or iStop>0:
                PrintTimeMsg("LoopAndWatchPrograms#%d.iStart=%s,iStop=%s!" % (
                    iLoopCnt,iStart,iStop))
            PrintAndSleep(self.iCheckIntervalSeconds,
                          "LoopAndWatchPrograms.iLoopCnt=%s=" % (iLoopCnt), iLoopCnt%10 == 0)

#--------------------------------------
def StartCWinSupervisor(srcfile, sPythonFileName, sDictVarName, sLongIdStr):
    ws = CWinSupervisor(srcfile, sPythonFileName, sDictVarName, sLongIdStr)
    ws.LoopAndWatchPrograms()

#--------------------------------------
if __name__ == '__main__':
    sPythonFileName = 'demoSettingsWinSV.py'
    sDictVarName = 'gDictConfigByGroupId'
    sLongIdStr = 'groupExample.programDirC,groupExample.programQQt'
    # sLongIdStr = 'groupExample.programQQ'
    # sLongIdStr = 'groupExample.programQQt'
    if len(sys.argv)>=4:
        sPythonFileName = sys.argv[1]
        sDictVarName = sys.argv[2]
        sLongIdStr = sys.argv[3]
    StartCWinSupervisor(__file__,sPythonFileName, sDictVarName, sLongIdStr)
