# -*- coding:utf-8 -*-
'''
Created on 2016-6-16
@author: Weber Juche

从 CHubCallbackBase 继承，实现了 P2PLayout 模式中一些基础服务。



'''
import gevent
from gevent.queue import Queue
from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep

from mGlobalConst import P2PKIND_P2PLAYOUT,CHAR_SEP_P2PLAYOUT
from cstpFuncs import GetCmdReplyFmRequest,CMDID_NOTIFY_MSG

from CHubCallbackQueueBase import CHubCallbackQueueBase

from mP2PLayoutConst import CMD0_P2PLAYOUT_SEND_CMD_TOPEER,CMD0_P2PLAYOUT_SEND_SYSTEM_MSG

#--------------------------------------
class CHubCallbackP2PLayout(CHubCallbackQueueBase):
    def __init__(self,sHubId, dictP2PLayoutByPairId):
        CHubCallbackQueueBase.__init__(self,sHubId)
        self.dictP2PLayoutByPairId = dictP2PLayoutByPairId
        self.lsPairIdAllow = set(self.dictP2PLayoutByPairId.keys()) #允许接入的PairId列表
        self.lsPairIdAllow.remove('@sPairId')

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
            return False,'sPairId=(%s) not in lsPairIdAllow!' % sPairId
        dictPasswdBySuffix = self.dictP2PLayoutByPairId.get(sPairId,{})
        if dictPasswdBySuffix:
            if dictPasswdBySuffix.get(sSuffix,'')!=sAcctPwd:
                return False,'sSuffix=(%s).password NOT match!' % sSuffix
            return True,''
        else:
            return False,'sPairId=(%s) NOT found!' % sPairId

    def SendP2PMsgToPeerByPairId(self, sPairId, sSuffixTo, CmdIStr):
        # 依据sPairId发送P2P消息， 返回 sErrno,sMsg 其中，sErrno='' 表示无错误
        sPeerIdTo = self.GetPeerIdFmPairId(sPairId, sSuffixTo)
        sClientIPPortTo = self.dictCIPByPeerId.get(sPeerIdTo,'')
        if not sClientIPPortTo:
            return '203','SendP2PMsgToPeerByPairId(%s,%s).sClientIPPortTo=NULL' % (sPairId, sSuffixTo)
        self.PutCmdStrToReturnQueue([sClientIPPortTo,CMDID_NOTIFY_MSG,CmdIStr])
        return '','OK'

    def BroadcastP2PMsgToSuffixSet(self, sPairId, setSuffix, CmdIStr):
        # 广播P2P消息到 setSuffix ,返回 sErrno,sMsg
        sErrno,sMsg = '','OK'
        iSndCnt = 0
        for sSuffix in setSuffix:
            sE,sM = self.SendP2PMsgToPeerByPairId(sPairId,sSuffix,CmdIStr)
            if sE!='' and sErrno=='': # 仅记录首个错误
                sErrno,sMsg = sE,sM
            else:
                iSndCnt += 1
        if sErrno=='':
            sMsg = 'OK(%d)' % iSndCnt
        return sErrno,sMsg

    def BroadcastP2PMsgByPairId(self, sPairId, sSuffix,CmdIStr):
        setSuffix = self.dictSuffixSetByPairId.get(sPairId,set([]))
        return self.BroadcastP2PMsgToSuffixSet(sPairId, setSuffix, CmdIStr)

    def CalcMatchSuffixSetFromTo(self, sPairId, sListSuffixTo):
        # 根据 sListSuffixTo 计算出匹配上的 sSuffixTo 集合
        setSuffix = self.dictSuffixSetByPairId.get(sPairId,set([]))
        if sListSuffixTo=='*': #全部广播
            return setSuffix
        lsPrefix = []
        lsTo = sListSuffixTo.split(',')
        for sTo in lsTo:
            (sToPrefix, cSep, sToSuffix) = sTo.partition('*')
            if cSep: #暂时仅匹配前缀
                lsPrefix.append(sToPrefix)
            else:
                lsPrefix.append(sTo)
        lsOut = []
        for sSuffix in setSuffix:
            for sP in lsPrefix:
                if sSuffix.startswith(sP):
                    lsOut.append(sSuffix)
        return set(lsOut)

    def SendP2PMsgToPeerByCIP(self, sClientIPPort, sSuffixFm, sListSuffixTo, CmdIStr):
        # 发送P2P消息， 返回 sErrno,sMsg 其中，sErrno='' 表示无错误
        sPairId = self.GetLinkAttrValue(sClientIPPort,'sPairId','')
        if not sPairId:
            return '202','SendP2PMsgToPeerByCIP.sPairId=NULL'
        if '@' in sListSuffixTo:
            return '204','SendP2PMsgToPeerByCIP.sSuffixTo include(@) Not supported!'
        setSuffix = self.CalcMatchSuffixSetFromTo(sPairId, sListSuffixTo)
        return self.BroadcastP2PMsgToSuffixSet(sPairId,setSuffix,CmdIStr)

    def DoHandleCheckAuthLayout(self, oLink, dwCmdId, sHubId,
                            sP2PKind, sAcctId, sAcctPwd, ynForceLogin, sClientInfo):
        # 处理客户端P1A/P1B鉴权，返回格式为:CmdOStr
        (sPairId, cSep, sSuffix) = sAcctId.partition(CHAR_SEP_P2PLAYOUT)
        sErrno,sMsg = '102','DefaultError'
        if cSep=='':
            sErrno = '110'
            sMsg = 'sAcctId=(%s)Format Error!' % sAcctId
        else:
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
                        CMD0_P2PLAYOUT_SEND_SYSTEM_MSG,
                        'PeerOnline',     #Action
                        sPairId,          #Pair标识
                        sSuffix,          #Pair后缀
                        sOnlineList,      #在线 sSuffix 列表串
                        GetCurrentTime(), #服务器时间
                    ]
                    self.BroadcastP2PMsgByPairId(sPairId, sSuffix, CmdIStr)

                    CmdOStr = ['OK',
                        sP2PKind,
                        sHubId,
                        sAcctId,
                        GetCurrentTime(),
                        'sServerInfo@P2PLayout',
                    ]
                    return CmdOStr
                else:
                    sErrno = '111'
                    sMsg = 'sPairId=%s,sSuffix=%s Already Login on (%s)!' % (
                        sPairId, sSuffix, sOldIPPort)
        CmdOStr = ['ES',   #0=系统错误，由框架断开链接
            sErrno,        #1=错误代码
            sMsg,          #2=错误提示信息
            'CHubCallbackP2PLayout.DoHandleCheckAuthP1', #3=错误调试信息
        ]
        return CmdOStr

    def DoHandleCheckAuth(self, oLink, dwCmdId, sHubId,
                            sP2PKind,sAcctId, sAcctPwd, ynForceLogin, sClientInfo):
         # 处理客户端鉴权，返回格式为: CmdOStr
        if sP2PKind==P2PKIND_P2PLAYOUT: #.startswith('P1'):
            CmdOStr = self.DoHandleCheckAuthLayout(oLink, dwCmdId, sHubId,
                            sP2PKind, sAcctId, sAcctPwd, ynForceLogin, sClientInfo)
        else:
            CmdOStr = CHubCallbackQueueBase.DoHandleCheckAuth(self,
                            oLink, dwCmdId, sHubId, sP2PKind,
                            sAcctId, sAcctPwd, ynForceLogin, sClientInfo)
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
            PrintTimeMsg('CHubCallbackP2PLayout.HandleClientEnd.sPairId=(%s),sSuffix=(%s)Nodo!' % (sPairId,sSuffix))
        sPeerId = self.GetLinkAttrValue(sClientIPPort,'sPeerId','')
        if sPeerId:
            del self.dictCIPByPeerId[sPeerId]
            PrintTimeMsg('CHubCallbackP2PLayout.HandleClientEnd.sPeerId=(%s),del(%s)!' % (sPeerId,sClientIPPort))
        else:
            PrintTimeMsg('CHubCallbackP2PLayout.HandleClientEnd.sPeerId=(%s)Nodo!' % (sPeerId))
        CHubCallbackQueueBase.HandleClientEnd(self,sClientIPPort)
        CmdIStr = [
            CMD0_P2PLAYOUT_SEND_SYSTEM_MSG,
            'PeerOffline',    #Action
            sPairId,          #Pair标识
            sSuffix,          #Pair后缀
            sOnlineList,      #在线 sSuffix 列表串
            GetCurrentTime(), #服务器时间
        ]
        self.BroadcastP2PMsgByPairId(sPairId, sSuffix,CmdIStr)

    def HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr):
        # 处理客户端请求命令
        bDone = CHubCallbackQueueBase.HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr)
        if not bDone:
            if CmdIStr[0]==CMD0_P2PLAYOUT_SEND_CMD_TOPEER:
                sErrno,sMsg = self.DoP2PLayoutSendCmdToPeer(sClientIPPort, dwCmdId, CmdIStr)
                if sErrno=='':
                    CmdOStr = ['OK','%s(%s)To(%s)=%s!' % (CMD0_P2PLAYOUT_SEND_CMD_TOPEER,sClientIPPort,CmdIStr[2],sMsg)]
                else:
                    CmdOStr = ['ES',   #0=系统错误，由框架断开链接
                        sErrno,        #1=错误代码
                        sMsg,          #2=错误提示信息
                        'CHubCallbackP2PLayout.HandleRequestCmd', #3=错误调试信息
                    ]
                dwCmdId = GetCmdReplyFmRequest(dwCmdId)
                self.PutCmdStrToReturnQueue([sClientIPPort,dwCmdId,CmdOStr])
                bDone = True
        return bDone

    def DoP2PLayoutSendCmdToPeer(self, sClientIPPort, dwCmdId, CmdIStr):
        # 向同一sPairId中的其它Peer发命令请求
        PrintTimeMsg('DoP2PLayoutSendCmdToPeer.CmdIStr=(%s)!' % (','.join(CmdIStr)))
        sSuffixFm = self.GetLinkAttrValue(sClientIPPort,'sSuffix','')
        sErrno = '202'
        sMsg = 'DoP2PLayoutSendCmdToPeer.sSuffixFm=%s, not matches (%s)!' % (sSuffixFm,CmdIStr[1])
        if sSuffixFm==CmdIStr[1]:
            sListSuffixTo = CmdIStr[2]
            sErrno,sMsg = self.SendP2PMsgToPeerByCIP(sClientIPPort,sSuffixFm,sListSuffixTo,CmdIStr) #原样送达
        return (sErrno,sMsg)



#--------------------------------------
def testMain():
    pass

if __name__=='__main__':
    testMain()