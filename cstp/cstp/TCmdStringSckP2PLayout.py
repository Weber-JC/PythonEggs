# -*- coding:utf-8 -*-
"""
Created on 2016-6-30
@author: Weber Juche

从 TCmdStringSck 继承，实现 P2P11 的客户端。

"""

from weberFuncs import PrintTimeMsg, GetCurrentTime, PrintAndSleep, printCmdString
from mGlobalConst import CMD0_ECHO_CMD,P2PKIND_P2PLAYOUT,CHAR_SEP_P2PLAYOUT
from TCmdStringSck import TCmdStringSck
from mP2PLayoutConst import CMD0_P2PLAYOUT_SEND_SYSTEM_MSG,CMD0_P2PLAYOUT_SEND_CMD_TOPEER

# 基于 CMD0_P2PLAYOUT_SEND_CMD_TOPEER 遍历报数请求
CMD3_P2PLAYOUT_TRAVERSE_COUNT = 'TraverseCount'
#  4=iCountValueNow  # 当前报数结果
#  5=sSuffixDoneList # 已经完成报数的 sSuffix 列表串，逗号分隔

#-------------------------------------------------
class TCmdStringSckP2PLayout(TCmdStringSck):

    def __init__(self, sHubId,sHostAndPort,sPairId,sSuffix,sAcctPwd,sClientInfo):
        self.sPairId = sPairId
        self.sSuffix = sSuffix
        self.sSuffixOnlineList = ''   #当前在线后缀列表
        sAcctId = sPairId+CHAR_SEP_P2PLAYOUT+sSuffix
        TCmdStringSck.__init__(self,sHubId,P2PKIND_P2PLAYOUT,sHostAndPort,sAcctId,sAcctPwd,'Y',sClientInfo)

    def LoopAndProcessLogic(self):
        iCnt = 0
        while True:
            sLogicParam = 'LogParam'+str(iCnt)
            #self.SendRequestCmd((CMD0_ECHO_CMD,'Just4Test',"python"+str(iCnt),sLogicParam),sLogicParam)
            iCnt += 1
            # if iCnt==5:
            #     self.SendNotifyMsg(("LmtApi.NotifyMsg",'Just4Test',"python"+str(iCnt),sLogicParam))
            # if iCnt==6:
            #     self.SendRequestCmd((CMD0_P2PLAYOUT_SEND_CMD_TOPEER,'B','TellMeCmd','Just4TestFromA',"python"+str(iCnt),sLogicParam))
            # if iCnt==7:
            #     self.SendRequestCmd((CMD0_P2PLAYOUT_SEND_CMD_TOPEER,'B,B','TellMeCmd2','Just4TestFromA',"python"+str(iCnt),sLogicParam))
            # if iCnt==8:
            #     self.SendRequestCmd((CMD0_P2PLAYOUT_SEND_CMD_TOPEER,'*','TellMeCmd*','Just4TestFromA',"python"+str(iCnt),sLogicParam))
            if (iCnt>=10): break #10
            #time.sleep(0.1)
        if self.sSuffix=='Test':
            self.LaunchTraverseCount()
            self.SendRequestCmd((CMD0_P2PLAYOUT_SEND_CMD_TOPEER,self.sSuffix,'B*,A,C,D','TellMeCmd2','Just4TestFromA',"python"+str(iCnt),sLogicParam))

    def OnHandleReplyCallBack(self,sCmd0,sLogicParam,CmdStr,dwCmdId):
        PrintTimeMsg("TCmdStringSckAppP1.OnHandleReplyCallBack.sCmd0=%s,dwCmdId=%s,sLogicParam=%s,CmdStr=%s"
                    % (sCmd0, dwCmdId, sLogicParam, str(CmdStr)) )
        return True

    def OnHandleNotifyCallBack(self,CmdStr,dwCmdId):
        # 供子类继承，用于接收并处理通知消息
        if CmdStr[0]==CMD0_P2PLAYOUT_SEND_SYSTEM_MSG:  #系统消息
            self.HandleSendSystemMsg(CmdStr)
        elif CmdStr[0]==CMD0_P2PLAYOUT_SEND_CMD_TOPEER: #预分配消息
            self.HandleSendCmdToPeer(CmdStr)
        else:
            TCmdStringSck.OnHandleNotifyCallBack(self,CmdStr,dwCmdId)

    def HandleSendSystemMsg(self, CmdStr):
        self.sSuffixOnlineList = CmdStr[4]
        PrintTimeMsg("HandleSendSystemMsg.CmdStr=%s=" % (','.join(CmdStr)) )

    def SendRequestP2PLayoutCmd(self, sSuffixTarget, CmdStr, sLogicParam):
        # 发送P2PLayout请求命令，格式参见 mP2PLayoutConst.py
        CmdIStr = [CMD0_P2PLAYOUT_SEND_CMD_TOPEER,self.sSuffix, sSuffixTarget]
        CmdIStr.extend(CmdStr)
        printCmdString('SendRequestP2PLayoutCmd=',CmdIStr)
        self.SendRequestCmd(CmdIStr,sLogicParam)

    # def SendRequestP2PLayoutCmdTraverseCount(self, CmdStr, sLogicParam):
    #     # 发送P2PLayout请求命令，格式参见 mP2PLayoutConst.py
    #     CmdIStr = [CMD3_P2PLAYOUT_TRAVERSE_COUNT,self.sSuffix]
    #     CmdIStr.append(CmdStr)
    #     self.SendRequestCmd(CmdIStr,sLogicParam)

    def HandleSendCmdToPeer(self, CmdStr):
        sSuffixFm = CmdStr[1]
        sSuffixTo = CmdStr[2]
        sPeerCmd = CmdStr[3]
        if sPeerCmd==CMD3_P2PLAYOUT_TRAVERSE_COUNT:
            self.DoTraverseCount(CmdStr)
        PrintTimeMsg("HandleSendCmdToPeer.CmdStr=%s=" % (','.join(CmdStr)) )

    def DoTraverseCount(self, CmdStr):
        iCountValueNow = int(CmdStr[4])
        self.sSuffixDoneList = CmdStr[5]
        lsSuffixDone = self.sSuffixDoneList.split(',')
        lsSuffixOnline = self.sSuffixOnlineList.split(',')
        lsSuffixDone.append(self.sSuffix)
        lsLeft = []
        for sS in lsSuffixOnline:
            if sS not in lsSuffixDone:
                lsLeft.append(sS)
        if len(lsLeft)<=0:
            PrintTimeMsg('DoTraverseCount.END!!!')
        else:
            iCountValueNow += 1
            sSuffixTarget = lsLeft[0]
            self.SendRequestP2PLayoutCmd(sSuffixTarget,
                                (CMD3_P2PLAYOUT_TRAVERSE_COUNT,
                                str(iCountValueNow),
                                ','.join(lsSuffixDone),),'sLogicParam')

    def LaunchTraverseCount(self):
        lsSuffixOnline = self.sSuffixOnlineList.split(',')
        lsLeft = []
        for sS in lsSuffixOnline:
            if sS != self.sSuffix:
                lsLeft.append(sS)
        if len(lsLeft)<=0:
            PrintTimeMsg('LaunchTraverseCount.lsLeft=(%s)!' % ','.join(lsLeft))
        else:
            PrintTimeMsg('LaunchTraverseCount.lsLeft=(%s)!' % ','.join(lsLeft))
            sSuffixTarget = lsLeft[0]
            iCountValueNow = 1
            self.SendRequestP2PLayoutCmd(sSuffixTarget,
                                (CMD3_P2PLAYOUT_TRAVERSE_COUNT,
                                str(iCountValueNow),
                                self.sSuffix,),'sLogicParam')

def TestTCmdStringSckP2PLayout():
    sHubId = 'fba008448317ea7f5c31f8e19c68fcf7'
    cssa = TCmdStringSckP2PLayout(sHubId,"127.0.0.1:8888",'one','Test','onePairTest','sClientDevInfo')
    cssa.StartMainThreadLoop()
#--------------------------------------
if __name__=='__main__':
    TestTCmdStringSckP2PLayout()
