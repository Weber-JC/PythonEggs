# -*- coding:utf-8 -*-
"""
Created on 2016-7-5
@author: Weber Juche

测试 TCmdStringSckP2PLayout 类。

"""

from weberFuncs import PrintTimeMsg, GetCurrentTime, PrintAndSleep

from cstp import TCmdStringSckP2PLayout

def TestTCmdStringSckP2PLayout():
    sHubId = '19ae99f03a6eaa51878a4335ec0d06ac'
    cssa = TCmdStringSckP2PLayout(sHubId,"127.0.0.1:9110",'MonitHub','Test.SendEMail','ts0928@1519','sClientDevInfo')
    cssa.SendRequestP2PLayoutCmd('!Service.SendMail',
                                 ['SendNotifyMail','weiyf1225@qq.com','Subject标题','Content内容','来自测试'],
                                 'LogicParam')
    cssa.StartMainThreadLoop()
#--------------------------------------
if __name__=='__main__':
    TestTCmdStringSckP2PLayout()
