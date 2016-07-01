# -*- coding:utf-8 -*-
"""
Created on 2016-6-30
@author: Weber Juche

从 TCmdStringSck 继承，实现 P2P11 的客户端。

"""

from weberFuncs import PrintTimeMsg, GetCurrentTime, PrintAndSleep
from mGlobalConst import CMD0_ECHO_CMD,P2PKIND_P2PLAYOUT,CHAR_SEP_P2PLAYOUT
from mP2PLayoutConst import CMD0_P2PLAYOUT_SEND_SYSTEM_MSG,CMD0_P2PLAYOUT_SEND_CMD_TOPEER
from TCmdStringSck import TCmdStringSck

#-------------------------------------------------
class TCmdStringSckP2PLayout(TCmdStringSck):

    def __init__(self, sHubId,sHostAndPort,sPairId,sSuffix,sAcctPwd,sClientInfo):
        sAcctId = sPairId+CHAR_SEP_P2PLAYOUT+sSuffix
        TCmdStringSck.__init__(self,sHubId,P2PKIND_P2PLAYOUT,sHostAndPort,sAcctId,sAcctPwd,'Y',sClientInfo)

    def LoopAndProcessLogic(self):
        iCnt = 0
        while True:
            sLogicParam = 'LogParam'+str(iCnt)
            #self.SendRequestCmd((CMD0_ECHO_CMD,'Just4Test',"python"+str(iCnt),sLogicParam),sLogicParam)
            iCnt += 1
            if iCnt==5:
                self.SendNotifyMsg(("LmtApi.NotifyMsg",'Just4Test',"python"+str(iCnt),sLogicParam))
            if iCnt==6:
                self.SendRequestCmd((CMD0_P2PLAYOUT_SEND_CMD_TOPEER,'B','TellMeCmd','Just4TestFromA',"python"+str(iCnt),sLogicParam))
            if iCnt==7:
                self.SendRequestCmd((CMD0_P2PLAYOUT_SEND_CMD_TOPEER,'B,B','TellMeCmd2','Just4TestFromA',"python"+str(iCnt),sLogicParam))
            if iCnt==8:
                self.SendRequestCmd((CMD0_P2PLAYOUT_SEND_CMD_TOPEER,'*','TellMeCmd*','Just4TestFromA',"python"+str(iCnt),sLogicParam))
            if (iCnt>=10): break #10
            #time.sleep(0.1)

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
        PrintTimeMsg("HandleSendSystemMsg.CmdStr=%s=" % (','.join(CmdStr)) )

    def HandleSendCmdToPeer(self, CmdStr):
        sSuffixFm = CmdStr[1]
        sSuffixTo = CmdStr[2]
        sPeerCmd = CmdStr[3]
        PrintTimeMsg("HandleSendCmdToPeer.CmdStr=%s=" % (','.join(CmdStr)) )

def TestTCmdStringSckP2PLayout():
    sHubId = 'fba008448317ea7f5c31f8e19c68fcf7'
    cssa = TCmdStringSckP2PLayout(sHubId,"127.0.0.1:8888",'one','A','onePairA','sClientDevInfo')
    cssa.StartMainThreadLoop()
#--------------------------------------
if __name__=='__main__':
    TestTCmdStringSckP2PLayout()
