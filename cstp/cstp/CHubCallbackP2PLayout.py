# -*- coding:utf-8 -*-
'''
Created on 2016-6-16
@author: Weber Juche

从 CHubCallbackBase 继承，实现了 P2PLayout 模式中一些基础服务。

'''
import sys
from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep

from mGlobalConst import P2PKIND_P2PLAYOUT,CHAR_SEP_P2PLAYOUT
from cstpFuncs import GetCmdReplyFmRequest,CMDID_NOTIFY_MSG
from cstpErrorFuncs import CSTPError,GenErrorTuple,GenOkMsgTuple
from CHubCallbackQueueBase import CHubCallbackQueueBase

from mGlobalConst import CMD0_KICK_OFFLINE
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
        # 返回 CmdOStr #bPass, sMsg
        sWhereMsg = 'CHubCallbackP2PLayout.CheckPairPwdStatus'
        if sPairId not in self.lsPairIdAllow:
            return GenErrorTuple(CSTPError.CHECK_AUTH_P2P_PAIRID_1, sWhereMsg,
                                 sPairId=sPairId)
        dictPasswdBySuffix = self.dictP2PLayoutByPairId.get(sPairId,{})
        if dictPasswdBySuffix:
            if dictPasswdBySuffix.get(sSuffix,'')!=sAcctPwd:
                return GenErrorTuple(CSTPError.CHECK_AUTH_P2P_SUFFIX_PWD, sWhereMsg,
                                     sSuffix=sSuffix)
            return GenOkMsgTuple(sWhereMsg)
        else:
            return GenErrorTuple(CSTPError.CHECK_AUTH_P2P_PAIRID_2, sWhereMsg,
                                 sPairId=sPairId)

    def SendP2PMsgToPeerByPairId(self, sPairId, sSuffixTo, CmdIStr):
        # 依据sPairId发送P2P消息， 返回 CmdOStr #sErrno,sMsg 其中，sErrno='' 表示无错误
        sWhereMsg = 'CHubCallbackP2PLayout.SendP2PMsgToPeerByPairId'
        sPeerIdTo = self.GetPeerIdFmPairId(sPairId, sSuffixTo)
        sClientIPPortTo = self.dictCIPByPeerId.get(sPeerIdTo,'')
        if not sClientIPPortTo:
            return GenErrorTuple(CSTPError.P2P_SEND_MSG_CIP_NOT_FOUND, sWhere,
                                 sPairId=sPairId, sPeerIdTo=sPeerIdTo)
        self.PutCmdStrToReturnQueue([sClientIPPortTo,CMDID_NOTIFY_MSG,CmdIStr])
        return GenOkMsgTuple(sWhereMsg)

    def BroadcastP2PMsgToSuffixSet(self, sPairId, setSuffix, CmdIStr):
        # 广播P2P消息到 setSuffix ,返回 CmdOStr
        sWhereMsg = 'CHubCallbackP2PLayout.BroadcastP2PMsgToSuffixSet'
        CmdOStrRet = GenOkMsgTuple(sWhereMsg)
        iSndCnt = 0
        PrintTimeMsg('BroadcastP2PMsgToSuffixSet.setSuffix=%s=' % str(setSuffix))
        for sSuffix in setSuffix:
            CmdOStr = self.SendP2PMsgToPeerByPairId(sPairId,sSuffix,CmdIStr)
            if CmdOStr[0]!='OK' and CmdOStrRet[0]=='OK':# 仅记录首个错误
                CmdOStrRet = CmdOStr
            else:
                iSndCnt += 1
        if CmdOStrRet[0]=='OK':
            lsRet = list(CmdOStrRet)
            lsRet[1] = 'SendP2PMsgCount=(%d)' % iSndCnt
            CmdOStrRet = tuple(lsRet)
        return CmdOStrRet

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
        # 发送P2P消息， 返回 CmdOStr
        sWhere = 'CHubCallbackP2PLayout.SendP2PMsgToPeerByCIP'
        sPairId = self.GetLinkAttrValue(sClientIPPort,'sPairId','')
        if not sPairId:
            return GenErrorTuple(CSTPError.P2P_SEND_MSG_CIP_NO_PAIRID, sWhere,
                                 sClientIPPort=sClientIPPort)
        if '@' in sListSuffixTo:
            return GenErrorTuple(CSTPError.P2P_SEND_MSG_NO_SUPPORT_0, sWhere,
                                 sListSuffixTo=sListSuffixTo)
        setSuffix = self.CalcMatchSuffixSetFromTo(sPairId, sListSuffixTo)
        return self.BroadcastP2PMsgToSuffixSet(sPairId,setSuffix,CmdIStr)

    def DoHandleCheckAuthLayout(self, oLink, dwCmdId, sHubId,
                            sP2PKind, sAcctId, sAcctPwd, ynForceLogin, sClientInfo):
        # 处理客户端P1A/P1B鉴权，返回格式为:CmdOStr
        sWhere = 'CHubCallbackP2PLayout.DoHandleCheckAuthLayout'
        CmdOStr = GenErrorTuple(CSTPError.CHECK_AUTH_DEFAULT, sWhere)
        (sPairId, cSep, sSuffix) = sAcctId.partition(CHAR_SEP_P2PLAYOUT)
        if cSep=='':
            CmdOStr = GenErrorTuple(CSTPError.CHECK_AUTH_P2P_ACCTID_FMT, sWhere,
                                    sAcctId=sAcctId)
        else:
            CmdOStr = self.CheckPairPwdStatus(sPairId, sSuffix, sAcctPwd)
            if CmdOStr[0]=='OK': #bPass:
                PrintTimeMsg('DoHandleCheckAuthP1.*******.dictCIPByPeerId=%s=' % str(self.dictCIPByPeerId))
                sPeerId = self.GetPeerIdFmPairId(sPairId, sSuffix)
                sOldIPPort = self.dictCIPByPeerId.get(sPeerId,'')
                if sOldIPPort=='' or ynForceLogin in 'Yy':
                    if sOldIPPort:
                        sReasonDesc = 'sP2PKind=%s,sPairId=%s,ynForceLogin=%s' % (sP2PKind,sPairId,ynForceLogin)
                        csKickOffline = [CMD0_KICK_OFFLINE, oLink.sClientIPPort, sOldIPPort, sReasonDesc]
                        self.PutCmdStrToReturnQueue([sOldIPPort,CMDID_NOTIFY_MSG,csKickOffline])
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
                    return ('OK',
                        sP2PKind,
                        sHubId,
                        sAcctId,
                        GetCurrentTime(),
                        'sServerInfo@P2PLayout',
                    )
                else:
                    return GenErrorTuple(CSTPError.CHECK_AUTH_P2P_ALREADY_ON, sWhere,
                                 sPairId=sPairId,sSuffix=sSuffix,sOldIPPort=sOldIPPort)
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
        bKickOff = self.GetLinkAttrValue(sClientIPPort,'bKickOff',False)
        if bKickOff:
            PrintTimeMsg("HandleClientEnd.sClientIPPort=(%s)bKickOff=True!" % (sClientIPPort))
        sOnlineList = ''
        sPairId = self.GetLinkAttrValue(sClientIPPort,'sPairId','')
        sSuffix = self.GetLinkAttrValue(sClientIPPort,'sSuffix','')
        if sPairId!='' and sSuffix!='':
            setSuffix = self.dictSuffixSetByPairId.get(sPairId,set([]))
            if not bKickOff:  setSuffix.remove(sSuffix)
            self.dictSuffixSetByPairId[sPairId] = setSuffix
            sOnlineList = ','.join(setSuffix)
        else:
            PrintTimeMsg('CHubCallbackP2PLayout.HandleClientEnd.sPairId=(%s),sSuffix=(%s)Nodo!' % (sPairId,sSuffix))
        sPeerId = self.GetLinkAttrValue(sClientIPPort,'sPeerId','')
        if sPeerId:
            if not bKickOff:  del self.dictCIPByPeerId[sPeerId]
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
                CmdOStr = self.DoP2PLayoutSendCmdToPeer(sClientIPPort, dwCmdId, CmdIStr)
                if CmdOStr[0]=='OK':
                    lsRet = list(CmdOStr)
                    lsRet[3] = '%s(%s)To(%s)!' % (CMD0_P2PLAYOUT_SEND_CMD_TOPEER,sClientIPPort,CmdIStr[2])
                    CmdOStr = tuple(lsRet)

                dwCmdId = GetCmdReplyFmRequest(dwCmdId)
                self.PutCmdStrToReturnQueue([sClientIPPort,dwCmdId,CmdOStr])
                bDone = True
        return bDone

    def DoP2PLayoutSendCmdToPeer(self, sClientIPPort, dwCmdId, CmdIStr):
        # 向同一sPairId中的其它Peer发命令请求
        # PrintTimeMsg('DoP2PLayoutSendCmdToPeer.CmdIStr=(%s)!' % (','.join(CmdIStr)))
        sSuffixFm = self.GetLinkAttrValue(sClientIPPort,'sSuffix','')
        if sSuffixFm==CmdIStr[1]:
            sListSuffixTo = CmdIStr[2]
            return self.SendP2PMsgToPeerByCIP(sClientIPPort,sSuffixFm,sListSuffixTo,CmdIStr) #原样送达
        else:
            sWhere = 'CHubCallbackP2PLayout.DoP2PLayoutSendCmdToPeer'
            return GenErrorTuple(CSTPError.P2P_SEND_MSG_SUFFIX_FM_ERR, sWhere,
                                 sSuffixFm=sSuffixFm, sSuffixFmHub=CmdIStr[1])

#--------------------------------------
def testMain():
    pass

if __name__=='__main__':
    testMain()