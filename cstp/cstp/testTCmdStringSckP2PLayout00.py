# -*- coding:utf-8 -*-
"""
Created on 2016-7-5
@author: Weber Juche

测试 TCmdStringSckP2PLayout 类。

"""

from weberFuncs import PrintTimeMsg, GetCurrentTime, PrintAndSleep

from TCmdStringSckP2PLayout import TCmdStringSckP2PLayout

def TestTCmdStringSckP2PLayout():
    sHubId = 'fba008448317ea7f5c31f8e19c68fcf7'
    cssa = TCmdStringSckP2PLayout(sHubId,"127.0.0.1:8888",'one','A','onePairA','sClientDevInfo')
    cssa.StartMainThreadLoop()
#--------------------------------------
if __name__=='__main__':
    TestTCmdStringSckP2PLayout()
