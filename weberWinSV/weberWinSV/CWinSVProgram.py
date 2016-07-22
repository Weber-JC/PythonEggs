#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
2016/7/20  WeiYanfeng
针对单个 cmdProgram=命令行程序 相关操作进行的封装。

-------- 依赖包
pip install psutil

"""

import sys
import os
import psutil #subprocess

from weberFuncs import PrintTimeMsg,GetCurrentTime,PrintAndSleep,PrintInline,PrettyPrintStr
from winsvFuncs import ReadTailLines,TerminateByPid

#-------------------------------------------------
class CWinSVProgram:
    def __init__(self, dictParam):
        self.dictParam = dictParam
        PrintTimeMsg("CWinSVProgram.dictParam=%s" % PrettyPrintStr(self.dictParam))
        self.sGroupId = self.dictParam.get('groupId','')
        self.sProgramId = self.dictParam.get('programId','')
        self.sCmdExec = self.dictParam.get('cmdExec','')
        self.sWorkDir = self.dictParam.get('workDir','')
        self.sLogDir = self.dictParam.get('logDir','')
        self.bErr2Out = self.dictParam.get('err2Out',True)
        self.bShellPopen = self.dictParam.get('shellPopen',False)

        PrintTimeMsg("CWinSVProgram.CWinSVProgram(%s.%s)=%s=" % (
            self.sGroupId, self.sProgramId, self.sCmdExec))
        PrintTimeMsg("CWinSVProgram.sWorkDir=%s=" % (self.sWorkDir))
        PrintTimeMsg("CWinSVProgram.sLogDir=%s=,bErr2Out=%s" % (self.sLogDir, self.bErr2Out))
        #   stopFile=<logDir>/<programId>.stop stop文件，若存在，则终止对应进程
        #   pidFile=<logDir>/<programId>.pid pid文件，用于查询该进程运行状态
        #   outFile=<logDir>/<programId>.out 标准输出日志文件
        #   errFile=<logDir>/<programId>.err 标准错误输出日志文件
        #   outerrFile=<logDir>/<programId>.tr 标准输出和错误输出合并日志文件

        sLogProgramId = self.sLogDir+self.sProgramId
        if self.bErr2Out:
            self.sLogOutFile = sLogProgramId+".tr"
            self.sLogErrFile = self.sLogOutFile
        else:
            self.sLogOutFile = sLogProgramId+".out"
            self.sLogErrFile = sLogProgramId+".err"
        self.sPidFile = sLogProgramId+".pid"
        self.sStopFile = sLogProgramId+".stop"

        try:
            sDir = self.sLogDir
            os.makedirs(sDir)
        except OSError as exc: # Python >2.5 (except OSError, exc: for Python <2.5)
            import errno
            if exc.errno == errno.EEXIST and os.path.isdir(sDir):
                pass
            else: raise

        self.fdOut = None
        self.fdErr = None
        self.Process = None #当前在运行的进程对象

        # self.bVerbose = False
        self.bVerbose = True

    def __del__(self):
        self.__closeFd()

    def CheckStopFileExists(self):
        # 检查 stop文件 是否存在
        sFN = self.sStopFile
        bRet = os.path.exists(sFN)
        if bRet:
            PrintTimeMsg("CheckStopFileExists(%s)=%s" % (sFN,bRet))
        return bRet

    def CrtDelStopFile(self, sAction):
        # 创建或删除 stop文件
        try:
            sFN = self.sStopFile
            if sAction=="DEL":
                if os.path.exists(sFN):
                    os.remove(sFN)
                    PrintTimeMsg("CrtDelStopFile.%s(%s)OK" % (sAction,sFN))
                else:
                    PrintTimeMsg("CrtDelStopFile.%s(%s)NotExists" % (sAction,sFN))
            else:
                if os.path.exists(sFN):
                    PrintTimeMsg("CrtDelStopFile.%s(%s)NotExists" % (sAction,sFN))
                else:
                    with open(sFN,"a") as f:
                        f.write('%s' % (GetCurrentTime())) #默认写入当前时间
                    PrintTimeMsg("CrtDelStopFile.%s(%s)OK" % (sAction,sFN))
        except OSError as e:
            PrintTimeMsg("CrtDelStopFile(%s)Error=(%s)!" % (self.sStopFile,str(e)))


    def CheckPidFileExists(self):
        # 检查 pid文件 是否存在
        bRet = os.path.exists(self.sPidFile)
        if not bRet:
            PrintTimeMsg("CheckPidFileExists(%s)=%s" % (self.sPidFile,bRet))
        return bRet

    def WritePidToFile(self,pid):
        # 输出 pid 文件
        try:
            with open(self.sPidFile,"w") as f: #覆盖模式输出
                sS = "%s" % (pid)
                f.write(sS)
            # PrintTimeMsg("_WritePidToFile(%s,%s)OK!" % (self.sPidFile,pid))
        except OSError as e:
            PrintTimeMsg("WritePidToFile(%s)Error=(%s)!" % (self.sPidFile,str(e)))

    def ReadPidFromFile(self):
        # 从文件中读取 pid
        try:
            with open(self.sPidFile,"r") as f: #覆盖模式输出
                sS = f.read()
                sS = sS.strip('\n')  #删除结尾换行
                pid = int(sS)
                # PrintTimeMsg("ReadPidFromFile(%s,%s)OK!" % (self.sPidFile,pid))
                return pid
        except OSError as e:
            PrintTimeMsg("ReadPidFromFile(%s)Error=(%s)!" % (self.sPidFile,str(e)))
            return -1

    def TouchPidFile(self):
        # 更新 pid文件 时间
        try:
            os.utime(self.sPidFile, None) #
            # PrintTimeMsg("TouchPidFile(%s)OK!" % (self.sPidFile))
        except OSError as e:
            PrintTimeMsg("TouchPidFile(%s)Error=(%s)!" % (self.sPidFile,str(e)))

    def GetPidFileTimeInt(self):
        # 读取 pid 文件修改时间
        try:
            # statinfo = os.stat('C:\\')
            # statinfo = os.stat('..\\test\\testXINA50.py')
            statinfo = os.stat(self.sPidFile)
            mtime = int(statinfo.st_mtime)
            # PrintTimeMsg("GetPidFileTimeInt(%s)=%s!" % (self.sPidFile,mtime))
            return mtime
        except OSError as e:
            PrintTimeMsg("GetPidFileTimeInt(%s)Error=(%s)!" % (self.sPidFile,str(e)))
            return -1

    def GetRedirectCmd(self):
        #WeiYF.20150603 这种方式需要 Shell=True 放弃
        sCmd = "%s 1> %s 2>&1" % (self.sCmdExec, self.sLogOutFile)
        PrintTimeMsg("GetRedirectCmd=(%s)" % (sCmd))
        return sCmd

    def ChangeWorkDir(self):
        # 更改工作目录
        sOldDir = os.getcwd()
        os.chdir(self.sWorkDir)
        sNewTmp = os.getcwd()
        # PrintTimeMsg("ChangeWorkDir(%s->%s)" % (sOldDir,sNewTmp))

    def GetLogFileInfo(self):
        # 返回日志文件信息
        try:
            # statinfo = os.stat('C:\\')
            # statinfo = os.stat('..\\test\\testXINA50.py')
            statinfo = os.stat(self.sLogOutFile)
            # PrintTimeMsg("GetLogFileInfo(%s)=%s!" % (self.sLogOutFile,statinfo))
            return statinfo
        except OSError as e:
            PrintTimeMsg("GetLogFileInfo(%s)Error=(%s)!" % (self.sLogOutFile,str(e)))
            return -1

    def __closeFd(self):
        if self.fdOut:
            self.fdOut.close()
            self.fdOut = None
        if self.fdErr:
            self.fdErr.close()
            self.fdErr = None

    def CheckAndRunOneCmd(self):
        # 检查并启动命令，适合于嵌入到主进程内运行
        #   返回+1，表示 启动了新程序
        #   返回-1，表示 停止了新程序
        #   返回0，表示 没变化
        self.ChangeWorkDir()
        # sCmd = self.getRedirectCmd()
        sCmd = self.sCmdExec
        if self.CheckStopFileExists():
            #Need Quit
            iRet = 0
            if self.CheckPidFileExists():
                pid = self.ReadPidFromFile()
                if psutil.pid_exists(pid):
                    TerminateByPid(pid)
                    iRet = -1
                else:
                    if self.bVerbose: PrintTimeMsg("Check(%s)AlreadyQuit.pid=(%s)..." % (sCmd,pid))
            else:
                PrintTimeMsg("checkPidFileExists.FALSE=(%s)..." % (sCmd))
            return iRet
        else:
            if self.CheckPidFileExists():
                pid = self.ReadPidFromFile()
                if psutil.pid_exists(pid):
                    self.TouchPidFile()
                    if self.bVerbose: PrintTimeMsg("Check(%s)StillRunning.pid=(%s)..." % (sCmd,pid))
                    return 0
            self.__closeFd()
            if self.bVerbose: PrintTimeMsg("CheckAndRunOneCmd.sLogOutFile=(%s)..." % (self.sLogOutFile))
            self.fdOut = open(self.sLogOutFile, 'a+')
            self.fdOut.write("\n[%s]%s{%s}...\n" % (GetCurrentTime(),'*'*40,self.sProgramId))
            self.fdOut.flush()
            if self.bErr2Out:
                self.fdErr = self.fdOut
            else:
                self.fdErr = open(self.sLogErrFile, 'a+')
            #self.Process = psutil.Popen(sCmd, stdout=self.fdOut,stderr=self.fdErr, shell=False) #True
            self.Process = psutil.Popen(sCmd, stdout=self.fdOut,stderr=self.fdErr, shell=self.bShellPopen)
            # Shell=True会新起一个cmd进程
            pid = self.Process.pid
            # sMsg = "%s#Start(%s)=%s" % (iStartCnt,sCmd,pid)
            # self.recordPopenLog(sMsg)
            PrintTimeMsg("Popen(%s)OK.pid=%s" % (sCmd,pid)) #[20:]
            self.WritePidToFile(pid)
            return +1

    # 如下函数用于 CWebSupervisor
    def GetLogTailTxt(self, nLine = 10):
        # 读取日志文件结尾若干行
        return ReadTailLines(self.sLogOutFile,nLine)

    def GetStatusDict(self):
        # 返回当前命令运行状态字典
        dictRet = self.dictParam
        pid = self.ReadPidFromFile()
        dictRet['pid'] = pid
        dictRet['pidExists'] = 'T' if psutil.pid_exists(pid) else 'F'
        dictRet['tmPidFile'] = self.GetPidFileTimeInt()
        statinfo = self.GetLogFileInfo()
        dictRet['tmLogFile'] = statinfo.st_mtime
        dictRet['szLogFile'] = statinfo.st_size
        # dictRet['logTail5'] = ReadTailLines(self.sLogOutFile,5)
        return dictRet

def testCWinSVProgram():
    dictParam = {  'cmdExec': u'ping juchecar.com',#  -t #dir C:\\
        'cmdTitle': u'\u8f6c\u9001\u884c\u60c5\u4fe1\u606f\u5230Redis',
        'endFlag': u'JustForEnd',
        'err2out': u'True',
        'groupId': u'groupId',
        'programId': u'ProgramId',
        'logDir': u'D:\\WeiYFGitSrc\\PythonProject\\WeberEgg\\GitHub_PythonEggs\\weberWinSV\\weberWinSV\\test\\log\\',
        'workDir': u'D:\\WeiYFGitSrc\\PythonProject\\WeberEgg\\GitHub_PythonEggs\\weberWinSV\\weberWinSV\\test\\'
    }
    c = CWinSVProgram(dictParam)
    c.CheckStopFileExists()
    c.CheckPidFileExists()
    c.GetRedirectCmd()
    c.GetPidFileTimeInt()
    c.GetLogFileInfo()
    print ReadTailLines(c.sLogOutFile,3) #10

    c.CrtDelStopFile("CRT")
    PrintAndSleep(10,"*** CrtDelStopFile")
    c.CrtDelStopFile("DEL")

    print c.CheckAndRunOneCmd()

#-------------------------------------------------
if __name__ == '__main__':
    testCWinSVProgram()