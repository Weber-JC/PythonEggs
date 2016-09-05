#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/8/26  WeiYanfeng
    实现了 TCmdPipeServer 和 P2PLayout模式下Peer端的对接。
"""

import sys

from weberFuncs import PrintTimeMsg
from TCmdStringSckP2PLayout import TCmdStringSckP2PLayout
from TCmdPipeServerTCBQ import TCmdPipeServerTCBQ

class TCmdStringSckP2PLayoutPipe(TCmdStringSckP2PLayout):
    def __init__(self, sHubId,sHostAndPort,sPairId,sSuffix,sAcctPwd,sClientInfo, iPrintIntervalNum,
                 iPipeServerPort,sPipeServerIP='127.0.0.1'):
        self.iPrintIntervalNum = iPrintIntervalNum #打印间隔数字, 越大日志越少
        self.bVerbose = self.iPrintIntervalNum<=0 #全部打印;
        TCmdStringSckP2PLayout.__init__(self,sHubId,sHostAndPort,sPairId,sSuffix,sAcctPwd,sClientInfo,self.bVerbose)
        PrintTimeMsg('TCmdStringSckP2PLayoutPipe.PipeServerIPPort=(%s:%s)' % (sPipeServerIP,iPipeServerPort))
        self.pipeServer = TCmdPipeServerTCBQ(iPipeServerPort,sPipeServerIP,self.HandlePipePushData)

    def HandlePipePushData(self, oData,iDealCount):
        if self.bVerbose:
            PrintTimeMsg('TCmdStringSckP2PLayoutPipe.HandlePipePushData.%d#.oData=%s=' % (iDealCount,oData))
        else:
            if iDealCount%self.iPrintIntervalNum==0:
                PrintTimeMsg('PipePushData#%d.oData=%s=' % (iDealCount,','.join(oData)))
        sRcv = '*'
        lsParam = [str(oData)]
        if type(oData)==list:
            sRcv = oData[0]
            lsParam = oData[1:]
        self.SendRequestP2PLayoutCmd(sRcv,lsParam,'sLogicParamPipe')
        # WeiYF.20160831 发送日志如下：
        # [2016-08-31 16:25:27.342]SerialCstCmdStrToString.dwCmdId=1978.CmdCnt=8={
        #   CmdStr[0].24=!P2PLayout.SendCmdToPeer=
        #   CmdStr[1].14=SndMinK.FeedIQ=
        #   CmdStr[2].9=RcvMinK.*=
        #   CmdStr[3].18=!MinuteK.PushRedis=
        #   CmdStr[4].9=kline_chg=
        #   CmdStr[5].13=XTIUSD_201610=
        #   CmdStr[6].1=N=
        #   CmdStr[7].77=20160831-162500.000554,46.07,46.07,46.05,46.07,95,81,C,20160831-162523.452846=
        # }
        # 可以看出，CmdStr[0]是固定命令，CmdStr[1]是发送者的sSuffix
        # CmdStr[2+]才是 TCmdPipeClient 填入的参数。

    def StartMainThreadLoop(self):
        TCmdStringSckP2PLayout.StartMainThreadLoop(self)
        # WeiYF.20160901 主循环退出时，使 pipeServer 也退出
        self.pipeServer.SetLoopRunFlagToQuit('StartMainThreadLoop.End!')
