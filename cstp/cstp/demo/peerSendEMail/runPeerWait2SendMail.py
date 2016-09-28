#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/7/7  WeiYanfeng
    在P2PLayout模式下，实现发送邮件的Peer
"""


import sys
import os
import random
from weberFuncs import PrintTimeMsg, GetCurrentTime, PrintAndSleep, GetCurrentTimeMSs, \
    WyfAppendToFile, CSendSMTPMail, CSerialJson, PrettyPrintStr
from weberFuncs import SimpleShiftDecode
from cstp import TCmdStringSckP2PLayout,StartCmdStringSckP2PLayout
from cstpPeerSettings import gDictPeerByParam
from smtpSettings import gDictSMTPByEMail

#-------------------------------------------------
# 参见 mP2PLayoutConst.py 说明：
# 基于 CMD0_P2PLAYOUT_SEND_CMD_TOPEER 实现发送电子邮件请求
CMD3_P2PLAYOUT_SEND_NOTIFY_MAIL = 'SendNotifyMail'
#  4=sToEMail        # 目标email，多个email可以采用英文分号分开
#  5=sSubject        # 邮件主题，utf-8编码
#  6=sContent        # 邮件内容，utf-8编码
#  7=sFromTitle      # 发件人名称，utf-8编码

#-------------------------------------------------
def GetThisFilePath(sSubDir=".", sFName=""):
    import os, sys, inspect
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe()))[0],sSubDir)))
    if sFName:
        return cmd_subfolder+os.sep+sFName
    return cmd_subfolder

class TPeerWait2SendMail(TCmdStringSckP2PLayout):

    def __init__(self, sHubId,sHostAndPort,sPairId,sSuffix,sAcctPwd,sClientInfo, bVerbosePrintCmdStr = True):
        global gDictSMTPByEMail
        TCmdStringSckP2PLayout.__init__(self,sHubId,sHostAndPort,sPairId,sSuffix,sAcctPwd,
                                        sClientInfo, bVerbosePrintCmdStr)
        iRunTimes = self.LoadAndSaveRunTimes()
        #sEMail = random.choice(gDictSMTPByEMail.keys())
        self.sSmtpEMail = gDictSMTPByEMail.keys()[iRunTimes % len(gDictSMTPByEMail)]
        PrintTimeMsg('TPeerWait2SendMail.iRunTimes=%d.sSmtpEMail=(%s)!' % (iRunTimes,self.sSmtpEMail))
        dictSMTP = gDictSMTPByEMail.get(self.sSmtpEMail,{})
        sKey = '20160811'
        sPass = SimpleShiftDecode(sKey,dictSMTP.get('pass',''))
        self.smtp = CSendSMTPMail(dictSMTP.get('smtp',''), self.sSmtpEMail, sPass)
        self.sFNameLogMailHistory = GetThisFilePath('./','logMailHistory.txt')
        PrintTimeMsg('TPeerWait2SendMail.sFNameLogMailHistory=(%s)!' % (self.sFNameLogMailHistory))
        WyfAppendToFile(self.sFNameLogMailHistory,'TPeerWait2SendMail.%s.pid=(%d)...' % ('-'*20,os.getpid()))
        self.TryToFinishSendMail()

    def DoHandleSendCmdToPeer(self, sSuffixFm,sSuffixTo,sPeerCmd,CmdStr):
        # 返回 True 表示已经处理过
        if sPeerCmd==CMD3_P2PLAYOUT_SEND_NOTIFY_MAIL:
            # self.smtp.SendMail(True,CmdStr[4],CmdStr[5],CmdStr[6],CmdStr[7])
            dictMail = {}
            dictMail['sToEMail'] = CmdStr[4]
            dictMail['sSubject'] = CmdStr[5]
            dictMail['sContent'] = CmdStr[6]
            dictMail['sFromTitle'] = CmdStr[7]
            # sMsg = PrettyPrintStr(dictMail)
            sMsg = ','.join(CmdStr[5:7])
            sMsg = sMsg.replace('\n',';')
            WyfAppendToFile(self.sFNameLogMailHistory,sMsg)
            self.SaveMailContentToSend(dictMail)
        else:
            return TCmdStringSckP2PLayout.DoHandleSendCmdToPeer(self, sSuffixFm,sSuffixTo,sPeerCmd,CmdStr)

    def LoadAndSaveRunTimes(self):
        iRunTimes = 0
        try:
            dictRunTimes = {}
            csjRunTimes = CSerialJson(GetThisFilePath('.','RunTimes.json'))
            PrintTimeMsg('LoadAndSaveRunTimes.sFNameSerial=(%s)!' % (csjRunTimes.sFNameSerial))
            try:
                dictRunTimes = csjRunTimes.Load()
                iRunTimes = dictRunTimes.get('iRunTimes',0)
                iRunTimes += 1
            except Exception, e:
                import traceback
                traceback.print_exc()
            dictRunTimes['iRunTimes'] = iRunTimes
            csjRunTimes.Save(dictRunTimes)
        except Exception, e:
            import traceback
            traceback.print_exc()
        return iRunTimes

    def TryToFinishSendMail(self):
        lsFN = os.listdir(GetThisFilePath('.'))
        for sFN in lsFN:
            if sFN.startswith('mailToSend'):
                sFNameMail = GetThisFilePath('.',sFN)
                self.SendMailAndDelFile(sFNameMail)


    def SaveMailContentToSend(self, dictMail):
        sFNameMail = GetThisFilePath('.','mailToSend%s.json' % GetCurrentTimeMSs())
        PrintTimeMsg('SaveMailContentToSend.sFNameMail=(%s)!' % (sFNameMail))
        try:
            csjMail = CSerialJson(sFNameMail)
            csjMail.Save(dictMail)
        except Exception, e:
            import traceback
            traceback.print_exc()
        self.SendMailAndDelFile(sFNameMail)

    def SendMailAndDelFile(self, sFNameMail):
        try:
            csjMail = CSerialJson(sFNameMail)
            dictMail = csjMail.Load()
            sToEMail = dictMail.get('sToEMail','')
            sSubject = dictMail.get('sSubject','')
            sContent = dictMail.get('sContent','')
            sFromTitle = dictMail.get('sFromTitle','')
            self.smtp.SendMail(True,sToEMail,sSubject,sContent,sFromTitle)
            os.remove(sFNameMail)
        except Exception, e:
            import traceback
            traceback.print_exc()

def runTPeerWait2SendMail(sHostName4Param, sAppId):
    global gDictPeerByParam
    StartCmdStringSckP2PLayout(gDictPeerByParam, sHostName4Param, sAppId, TPeerWait2SendMail)

#--------------------------------------
if __name__=='__main__':
    sHostName4Param = 'LocalTest'
    sHostName4Param = 'RunOnHost'
    sAppId = 'Wait2SendMail'
    if len(sys.argv)>=3:
        sHostName4Param = sys.argv[1]
        sAppId = sys.argv[2]
    runTPeerWait2SendMail(sHostName4Param,sAppId)