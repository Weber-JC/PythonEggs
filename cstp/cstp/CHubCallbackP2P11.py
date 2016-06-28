# -*- coding:utf-8 -*-
'''
Created on 2016-6-16
@author: Weber Juche

从 CHubCallbackBase 继承，实现了P2P的一些基础服务

'''
import gevent
from gevent.queue import Queue
from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep
from cstpFuncs import GetCmdReplyFmRequest,CMDID_NOTIFY_MSG,\
    CMD0_P2P11_SEND_CMD_TOPEER,CMD0_P2P11_SEND_SYSTEM_MSG

from CHubCallbackQueueBase import CHubCallbackQueueBase

#--------------------------------------
class CHubCallbackP2P11(CHubCallbackQueueBase):
    def __init__(self,sHubId, lsPairIdAllow):
        CHubCallbackQueueBase.__init__(self,sHubId)

        self.lsPairIdAllow = set(lsPairIdAllow) #允许接入的PairId列表

        self.dictCIPByPeerId = {} #以 PeerId=(sPairId+sSuffix) 为 Key 存储 sClientIPPort
        self.dictSuffixSetByPairId = {} #以 sPairId 为 Key 存储 sSuffix 的集合

    def GetPeerIdFmPairId(self, sPairId, sSuffix):
        # WeiYF.20160624 考虑到从 sPairId,sSuffix 计算sPeerId，还是频繁发生的
        #                所以这里采用简单串相加的算法，不采用md5
        #return md5(self.sHubId+sPairId+sSuffix+'@salt')
        return '%s|%s' % (self.sHubId+sPairId, sSuffix)

    def CheckPairPwdStatus(self, sPairId, sSuffix, sAcctPwd):
        # 返回 bPass, sMsg
        if sPairId not in self.lsPairIdAllow:
            return False,'sPairId=(%s) not in lsPairIdAllow!'
        sPairIdSuffix = '%s.%s' % (sPairId, sSuffix)
        dictPairPass = {
            'one.A':'onePairA',
            'one.B':'onePairB',
        }
        if dictPairPass.get(sPairIdSuffix,'')!=sAcctPwd:
            return False,'sPairIdSuffix=(%s) password NOT match' % sPairIdSuffix
        return True,''

    def SendP2P11MsgToPeerByPairId(self, sPairId, sSuffixTo, CmdIStr):
        # 依据sPairId发送P2P消息， 返回 sErrno,sMsg 其中，sErrno='' 表示无错误
        sPeerIdTo = self.GetPeerIdFmPairId(sPairId, sSuffixTo)
        sClientIPPortTo = self.dictCIPByPeerId.get(sPeerIdTo,'')
        if not sClientIPPortTo:
            return '203','SendP2P11MsgToPeerByPairId(%s,%s).sClientIPPortTo=NULL' % (sPairId, sSuffixTo)
        self.PutCmdStrToReturnQueue([sClientIPPortTo,CMDID_NOTIFY_MSG,CmdIStr])
        return '','OK'

    def SendP2P11MsgToPeerByCIP(self, sClientIPPort, sSuffixFm, sSuffixTo, CmdIStr):
        # 发送P2P消息， 返回 sErrno,sMsg 其中，sErrno='' 表示无错误
        sPairId = self.GetLinkAttrValue(sClientIPPort,'sPairId','')
        if not sPairId:
            return '202','SendP2POneToOneMsg.sPairId=NULL'
        sErrno,sMsg = '','OK'
        if sSuffixTo=='*':
            self.BroadcastP2P11MsgByPairId(sPairId,sSuffixFm,CmdIStr)
            return sErrno,sMsg
        lsTo = sSuffixTo.split(',')
        for sTo in lsTo:
            if sTo:
                sE,sM = self.SendP2P11MsgToPeerByPairId(sPairId,sTo,CmdIStr)
                if sE!='' and sErrno=='':
                    sErrno,sMsg = sE,sM
        return sErrno,sMsg

    def BroadcastP2P11MsgByPairId(self, sPairId, sSuffixFm, CmdIStr):
        # 按 sPairId 分组广播P2P消息， 无返回
        setSuffix = self.dictSuffixSetByPairId.get(sPairId,set([]))
        for sSuffix in setSuffix:
            self.SendP2P11MsgToPeerByPairId(sPairId,sSuffix,CmdIStr)

    def DoHandleCheckAuthP1(self, oLink, dwCmdId, sHubId,
                            sP2PKind, sPairId, sAcctPwd, ynForceLogin, sClientInfo):
        # 处理客户端P1A/P1B鉴权，返回格式为:CmdOStr
        sSuffix = sP2PKind[2:]
        sErrno = '102'
        bPass,sMsg = self.CheckPairPwdStatus(sPairId, sSuffix, sAcctPwd)
        if bPass:
            sPeerId = self.GetPeerIdFmPairId(sPairId, sSuffix)
            sOldIPPort = self.dictCIPByPeerId.get(sPeerId,'')
            if sOldIPPort=='' or ynForceLogin in 'Yy':
                setSuffix = self.dictSuffixSetByPairId.get(sPairId,set([]))
                setSuffix.add(sSuffix)
                self.dictSuffixSetByPairId[sPairId] = setSuffix
                oLink.sPeerId = sPeerId #链接对象保留 sPeerId 消息
                oLink.sPairId = sPairId
                oLink.sSuffix = sSuffix
                self.dictCIPByPeerId[sPeerId] = oLink.sClientIPPort
                PrintTimeMsg('DoHandleCheckAuthP1.dictCIPByPeerId=%s=' % str(self.dictCIPByPeerId))
                sOnlineList = ','.join(setSuffix)
                #发送上线通知消息
                CmdIStr = [
                    CMD0_P2P11_SEND_SYSTEM_MSG,
                    'PeerOnline',     #Action
                    sPairId,          #Pair标识
                    sSuffix,          #Pair后缀
                    sOnlineList,      #在线 sSuffix 列表串
                    GetCurrentTime(), #服务器时间
                ]
                self.BroadcastP2P11MsgByPairId(sPairId, sSuffix, CmdIStr)

                CmdOStr = ['OK',
                    sP2PKind,
                    sHubId,
                    sPairId,
                    GetCurrentTime(),
                    'sServerInfo@P2P11',
                ]
                return CmdOStr
            else:
                sErrno = '111'
                sMsg = 'sPairId=%s,sSuffix=%s Already Login on (%s)!' % (
                    sPairId, sSuffix, sOldIPPort)
        CmdOStr = ['ES',   #0=系统错误，由框架断开链接
            sErrno,        #1=错误代码
            sMsg,          #2=错误提示信息
            'CHubP2POneToOne.DoHandleCheckAuthP1', #3=错误调试信息
        ]
        return CmdOStr

    def HandleClientEnd(self, sClientIPPort):
        sOnlineList = ''
        sPairId = self.GetLinkAttrValue(sClientIPPort,'sPairId','')
        sSuffix = self.GetLinkAttrValue(sClientIPPort,'sSuffix','')
        if sPairId!='' and sSuffix!='':
            setSuffix = self.dictSuffixSetByPairId.get(sPairId,set([]))
            setSuffix.remove(sSuffix)
            self.dictSuffixSetByPairId[sPairId] = setSuffix
            sOnlineList = ','.join(setSuffix)
        else:
            PrintTimeMsg('CHubCallbackP2P11.HandleClientEnd.sPairId=(%s),sSuffix=(%s)Nodo!' % (sPairId,sSuffix))
        sPeerId = self.GetLinkAttrValue(sClientIPPort,'sPeerId','')
        if sPeerId:
            del self.dictCIPByPeerId[sPeerId]
            PrintTimeMsg('CHubCallbackP2P11.HandleClientEnd.sPeerId=(%s),del(%s)!' % (sPeerId,sClientIPPort))
        else:
            PrintTimeMsg('CHubCallbackP2P11.HandleClientEnd.sPeerId=(%s)Nodo!' % (sPeerId))
        CHubCallbackQueueBase.HandleClientEnd(self,sClientIPPort)
        CmdIStr = [
            CMD0_P2P11_SEND_SYSTEM_MSG,
            'PeerOffline',    #Action
            sPairId,          #Pair标识
            sSuffix,          #Pair后缀
            sOnlineList,      #在线 sSuffix 列表串
            GetCurrentTime(), #服务器时间
        ]
        self.BroadcastP2P11MsgByPairId(sPairId, sSuffix,CmdIStr)

    def DoHandleCheckAuth(self, oLink, dwCmdId, sHubId,
                            sP2PKind,sAcctId, sAcctPwd, ynForceLogin, sClientInfo):
         # 处理客户端鉴权，返回格式为: CmdOStr
        if sP2PKind.startswith('P1'):
            CmdOStr = self.DoHandleCheckAuthP1(oLink, dwCmdId, sHubId,
                            sP2PKind, sAcctId, sAcctPwd, ynForceLogin, sClientInfo)
        else:
            CmdOStr = CHubCallbackQueueBase.DoHandleCheckAuth(self,
                            oLink, dwCmdId, sHubId, sP2PKind,
                            sAcctId, sAcctPwd, ynForceLogin, sClientInfo)
        return CmdOStr

    def HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr):
        # 处理客户端请求命令
        bDone = CHubCallbackQueueBase.HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr)
        if not bDone:
            sErrno = '201'
            sMsg = '%s.Error!' % CMD0_P2P11_SEND_CMD_TOPEER
            if CmdIStr[0]==CMD0_P2P11_SEND_CMD_TOPEER:
                PrintTimeMsg('HandleRequestCmd.CmdIStr=(%s)!' % (','.join(CmdIStr)))
                sSuffixFm = self.GetLinkAttrValue(sClientIPPort,'sSuffix','')
                sSuffixTo = CmdIStr[1]
                CmdIStr.insert(1,sSuffixFm) #将发送者插入CmdIStr[1]
                sErrno,sMsg = self.SendP2P11MsgToPeerByCIP(sClientIPPort,sSuffixFm,sSuffixTo,CmdIStr) #原样送达
                if sErrno=='':
                    CmdOStr = ['OK','%s(%s)To(%s)' % (CMD0_P2P11_SEND_CMD_TOPEER,sClientIPPort,sSuffixTo)]
                else:
                    CmdOStr = ['ES',   #0=系统错误，由框架断开链接
                        sErrno,        #1=错误代码
                        sMsg,          #2=错误提示信息
                        'CHubCallbackP2P11.HandleRequestCmd', #3=错误调试信息
                    ]
                dwCmdId = GetCmdReplyFmRequest(dwCmdId)
                self.PutCmdStrToReturnQueue([sClientIPPort,dwCmdId,CmdOStr])
                bDone = True
        return bDone


#--------------------------------------
def testCHubCallbackP2PBase():
    bhc = CHubCallbackP2PBase() #oObj

if __name__=='__main__':
    testCHubCallbackP2PBase()