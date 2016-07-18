# -*- coding:utf-8 -*-
"""
Created on 2016-6-30
@author: Weber Juche

从 TCmdStringSck 继承，实现 P2P11 的客户端。

"""
import sys
from weberFuncs import PrintTimeMsg, GetCurrentTime, PrintAndSleep, printCmdString
from mGlobalConst import CMD0_ECHO_CMD,P2PKIND_P2PLAYOUT,CHAR_SEP_P2PLAYOUT
from TCmdStringSck import TCmdStringSck
from mP2PLayoutConst import CMD0_P2PLAYOUT_SEND_SYSTEM_MSG,CMD0_P2PLAYOUT_SEND_CMD_TOPEER

#-------------------------------------------------
# 参见 mP2PLayoutConst.py 说明：
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
        self.iOneSecondClock = 0

    def LoopAndProcessLogic(self):
        while not self.gef.IsExitFlagTrue():
            self.DoLoopOneSecondLogic()

    def DoLoopOneSecondLogic(self):
        self.iOneSecondClock += 1
        PrintAndSleep(1,'DoLoopOneSecondLogic.iOneSecondClock=%d' % self.iOneSecondClock,
                        self.iOneSecondClock%600==1) #10分钟打印一次日志
        if self.sSuffix=='Test':
            self.TestLaunchTraverseCount(self.iOneSecondClock)
        pass

    def TestLaunchTraverseCount(self, iLoopCnt):
        self.LaunchTraverseCount()
        sLogicParam = 'LogParam@'+str(iLoopCnt)
        self.SendRequestP2PLayoutCmd('B*,A,C,D',['TellMeCmd2','Just4TestFromA',"python"+str(iLoopCnt)],sLogicParam)
        self.SendRequestP2PLayoutCmd('A',['SendNotifyMail','weiyf1225@qq.com',
                                          '标题title','内容Content','sFromTitle测试'],sLogicParam)

    def OnHandleReplyCallBack(self,sCmd0,sLogicParam,CmdStr,dwCmdId):
        #WeiYF.20150715 为避免日志过多，暂时不打印
        # PrintTimeMsg("TCmdStringSckP2PLayout.OnHandleReplyCallBack.sCmd0=%s,dwCmdId=%s,sLogicParam=%s,CmdStr=%s"
        #             % (sCmd0, dwCmdId, sLogicParam, str(CmdStr)) )
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
        # PrintTimeMsg("HandleSendSystemMsg.CmdStr=%s=" % (','.join(CmdStr)) )

    def SendRequestP2PLayoutCmd(self, sSuffixTarget, CmdStr, sLogicParam):
        # 发送P2PLayout请求命令，格式参见 mP2PLayoutConst.py
        CmdIStr = [CMD0_P2PLAYOUT_SEND_CMD_TOPEER,self.sSuffix, sSuffixTarget]
        CmdIStr.extend(CmdStr)
        # printCmdString('TCmdStringSckP2PLayout.SendRequestP2PLayoutCmd=',CmdIStr)
        # WeiYF.20160715 为避免日志过多
        self.SendRequestCmd(CmdIStr,sLogicParam)

    def HandleSendCmdToPeer(self, CmdStr):
        sSuffixFm = CmdStr[1]
        sSuffixTo = CmdStr[2]
        sPeerCmd = CmdStr[3]
        if sPeerCmd==CMD3_P2PLAYOUT_TRAVERSE_COUNT:
            self.DoTraverseCount(sSuffixFm,sSuffixTo,sPeerCmd,CmdStr)
        else:
            self.DoHandleSendCmdToPeer(sSuffixFm,sSuffixTo,sPeerCmd,CmdStr)

    def DoHandleSendCmdToPeer(self, sSuffixFm,sSuffixTo,sPeerCmd,CmdStr):
        # 返回 True 表示已经处理过
        PrintTimeMsg("DoHandleSendCmdToPeer.CmdStr=%s=" % (','.join(CmdStr)) )
        return False

    def DoTraverseCount(self, sSuffixFm,sSuffixTo,sPeerCmd,CmdStr):
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

#--------------------------------------
def TestTCmdStringSckP2PLayout():
    sHubId = 'fba008448317ea7f5c31f8e19c68fcf7'
    cssa = TCmdStringSckP2PLayout(sHubId,"127.0.0.1:8888",'one','Test','onePairTest','sClientDevInfo')
    cssa.StartMainThreadLoop()

#--------------------------------------
# WeiYF.20160708 将启动过程封装为一个共享函数，其中 dictPeerByParam 格式如下：
# gDictPeerByParam = {
#    # CSTP Peer运行参数，以 sHostName4Param 为键值
#     'LocalTest': {  #本地环境  #sHostName4Param
#         'sIPPort': '127.0.0.1:8888',
#         'sHubId': 'fba008448317ea7f5c31f8e19c68fcf7',
#         'sPairId': 'one',
#         'Wait2SendMail' :{  # sAppId
#             'sSuffix': 'A',
#             'sAcctPwd': 'onePairA',
#             'sClientInfo': 'sClientDevInfo',
#         },
#     },
# }
#
def StartCmdStringSckP2PLayout(dictPeerByParam, sHostName4Param, sAppId, clsSckP2PLayout):
    dictParam = dictPeerByParam.get(sHostName4Param,{})
    if not dictParam:
        PrintTimeMsg('StartCmdStringSckP2PLayout.get(%s)={}' % sHostName4Param)
        sys.exit(-1)
    dictApp = dictParam.get(sAppId,{})
    if not dictApp:
        PrintTimeMsg('StartCmdStringSckP2PLayout.get(%s)From(%s)={}' % (sAppId, str(dictParam)))
        sys.exit(-1)
    sIPPort = dictParam.get('sIPPort', '')
    sHubId = dictParam.get('sHubId', '')
    sPairId = dictParam.get('sPairId', '')
    sSuffix = dictApp.get('sSuffix', '')
    sAcctPwd = dictApp.get('sAcctPwd', '')
    sClientInfo = dictApp.get('sClientInfo', '')
    if sIPPort and sHubId and sPairId and sSuffix:
        cssa = clsSckP2PLayout(sHubId,sIPPort,sPairId,sSuffix,sAcctPwd,sClientInfo)
        cssa.StartMainThreadLoop()
    else:
        sErrMsg = ''
        if not sIPPort: sErrMsg += 'sIPPort,'
        if not sHubId: sErrMsg += 'sHubId,'
        if not sPairId: sErrMsg += 'sPairId,'
        if not sSuffix: sErrMsg += 'sSuffix,'
        sErrMsg = '(%s) is null' % sErrMsg[:-1] #剔除最后一个逗号
        PrintTimeMsg('StartCmdStringSckP2PLayout.sErrMsg=%s!' % (sErrMsg))
        sys.exit(-1)


#--------------------------------------
if __name__=='__main__':
    TestTCmdStringSckP2PLayout()
