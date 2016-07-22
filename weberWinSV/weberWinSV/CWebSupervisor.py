#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
    2016/7/21  WeiYanfeng
    在Windows下启动并控制其它命令行程序(cmdProgram)运行
    类似于Linux系统下的 Supervisor 工具

    简化实现方式：
      1.WebServer启动时，启动 runRepeatConfigBat.py 并记录其进程号；
      2.WebServer提供对该进程提供 停止、重启服务；
      3.WebServer提供核心进程状态查询服务；

    实现原理描述：
      1.从当前目录下 configCmd.json 中读取要管理的程序；
      2.检查对应的pid文件是否存在，若pid文件存在且对应pid也存在，则跳过。
      3.否则采用NoWait方式启动对应程序，并记录其pid到pid文件。
      4.同时该启动程序会将程序输出重定向到日志文件，并在对应程序退出情况下，将其自动重启。
      5.提供URL，能够：A)查询到服务程序状态；B)暂停、启动、重启指定服务；
"""
import _addpath
import sys

import os
import time

import json
from cpyf.publicFuncs import PrintTimeMsg,GetCurrentTime,PrettyPrintStr,GetUnixTimeLocal

# import psutil

from CRepeatRunForWeb import CRepeatRunForWeb

######################################################
from local_bottle import route, template, response, request, static_file, \
    auth_basic, parse_auth

gCmdUrlPrefix = "/cmd"  #URL前缀

gRRFW = CRepeatRunForWeb("configCmd.json") #缺省配置文件
gRRFW.ProgramCheckRun()

def html_ListProgramAll(numTx = 100):
    global gRRFW
    # return "<pre>%s</pre>" % PrettyPrintStr(gRRFW.ProgramQueryAll())

    sRows = u'<tr><th>状态描述</th><th>备注</th><th>程序名</th><th>操作</th></tr>\n'
    dictAll = gRRFW.ProgramQueryAll(False)
    for programId,dictStatus in dictAll.items():
        cmdExec = dictStatus.get("cmdExec","")
        cmdTitle = dictStatus.get("cmdTitle","")
        # logTail5 = dictStatus.get("logTail5","")
        pid = dictStatus.get("pid",0)
        bPidExists = dictStatus.get("pidExists",'F')=='T'
        szLogFile = dictStatus.get("szLogFile",0)
        tmPidFile = dictStatus.get("tmPidFile",0)
        sStatus = ''
        if time.time()-tmPidFile>60:
            if bPidExists:
                sStatus = 'Wrong'
            else:
                sStatus = "Suspend"
        else:
            if bPidExists:
                sStatus = 'Running'
            else:
                sStatus = "JustQuit"
        sTimePid = GetUnixTimeLocal(int(tmPidFile))
        sD = sTimePid[0:8]
        sT = sTimePid[-6:]
        sTm = '%s-%s-%s %s:%s:%s' % (sD[0:4],sD[4:6],sD[6:8],sT[0:2],sT[2:4],sT[4:6])
        htmlDesc = '%s@%s [%s]' % (sStatus,sTm,pid)
        htmlMemo = cmdTitle
        htmlName = '<a href="%s/" title="%s">%s</a>' % (gCmdUrlPrefix, cmdExec, programId)
        htmlRestart = '<a href="%s/ProgramRestart/%s">Restart</a>' % (gCmdUrlPrefix, programId)
        htmlStop = '<a href="%s/ProgramStop/%s">Stop</a>' % (gCmdUrlPrefix, programId)
        htmlStart = '<a href="%s/ProgramStart/%s">Start</a>' % (gCmdUrlPrefix, programId)
        # htmlStartStop = htmlStop if bPidExists else htmlStart
        if bPidExists:
            htmlStart = ''
        htmlLogTailTxt = '<a href="%s/GetLogTailTxt/%s">TailTxt</a>' % (gCmdUrlPrefix, programId)
        htmlAction = '%s %s %s %s' % (htmlRestart, htmlStart, htmlStop, htmlLogTailTxt)

        #a_AddressTxid = '<a href="https://blockchain.info/tx/%s" target ="_blank">%s</a>' % (txId,sAddress)
        sRow = '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' % (
                htmlDesc, htmlMemo, htmlName, htmlAction)
        sRows += sRow
    return '<div align="center"><table border="0" cellspacing="1" class="table-striped">\n%s</table></div>\n' % (sRows)


######################################################
def checkUserPasswd(sUser, sPasswd):
    sClientIP = request.environ.get('REMOTE_ADDR','')
    sAddition = "%s,%s" % (request.url,request.remote_route)
    sMsg = "user=%s,passwd=%s,memo=%s" % (sUser,sPasswd,sAddition)
    sTag = "Deny"
    bRet = (sUser=="btcTws" and sPasswd=="796796")
    if bRet:
        sTag = "Pass"
        sMsg = "memo=%s" % (sAddition)
    with open("ip_check.txt","a") as f: #追加模式输出
        sS = "[%s]%s:%s\t#%s\n" % (GetCurrentTime(),sTag, sClientIP, sMsg)
        f.write(sS)
    return bRet
######################################################
@route(gCmdUrlPrefix)
@route(gCmdUrlPrefix+'/')
@auth_basic(checkUserPasswd)
def cmdRoot():
    # print gRRFW.ProgramCheckRun()
    return html_ListProgramAll()

@route(gCmdUrlPrefix+'/ProgramCheckRun')
def cmdProgramCheckRun():
    global gRRFW
    bRet = gRRFW.ProgramCheckRun()
    sRet = "Ignore"
    if bRet:
        sRet = "Check"
    return sRet

def getHtmlHome():
    global gCmdUrlPrefix
    return '<a href="%s">ReturnBack</a>' % (gCmdUrlPrefix)

@route(gCmdUrlPrefix+'/GetLogTailTxt/<sProgramId>')
@auth_basic(checkUserPasswd)
def cmdGetLogTailTxt(sProgramId):
    global gRRFW
    # print gRRFW.ProgramCheckRun()
    lsLines = gRRFW.ProgramGetLogTailTxt(sProgramId)
    sText = ''
    for sLine in lsLines:
        sText += sLine
    return '<pre>%s</pre>%s' % (sText,getHtmlHome())


@route(gCmdUrlPrefix+'/ProgramStop/<sProgramId>')
@auth_basic(checkUserPasswd)
def cmdProgramStop(sProgramId):
    global gRRFW
    bRet = gRRFW.ProgramStopOne(sProgramId)
    gRRFW.ProgramCheckRun(True)
    return 'ProgramStopOne(%s)=(%s)<br/>%s' % (sProgramId,bRet,getHtmlHome())

@route(gCmdUrlPrefix+'/ProgramStart/<sProgramId>')
@auth_basic(checkUserPasswd)
def cmdProgramStart(sProgramId):
    global gRRFW
    bRet = gRRFW.ProgramStartOne(sProgramId)
    gRRFW.ProgramCheckRun(True)
    return 'ProgramStartOne(%s)=(%s)<br/>%s' % (sProgramId,bRet,getHtmlHome())

@route(gCmdUrlPrefix+'/ProgramRestart/<sProgramId>')
@auth_basic(checkUserPasswd)
def cmdProgramRetart(sProgramId):
    global gRRFW
    bRet = gRRFW.ProgramStartOne(sProgramId)
    gRRFW.ProgramCheckRun(True)
    return 'ProgramStartOne(%s)=(%s)<br/>%s' % (sProgramId,bRet,getHtmlHome())

if __name__ == '__main__':
    print html_ListProgramAll()
