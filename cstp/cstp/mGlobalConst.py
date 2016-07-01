#!/usr/local/bin/python
#-*- coding:utf-8 -*-

"""
Created on 2016-7-1
@author: Weber Juche

    定义了一些全局命令字常量
"""

# import sys
# from weberFuncs import PrintTimeMsg

#---------------------------------
CMD0_CHECK_AUTH = '!CSTP.CheckAuth' # 检查接入授权命令字
CMD0_ECHO_CMD = '!CSTP.EchoCmd' # 接入框架回声命令字，能则实现

#sP2PKind 取值
P2PKIND_ACCTSHARE = 'AcctShare'
P2PKIND_P2PCOMMON = 'P2PCommon'
P2PKIND_P2PLAYOUT = 'P2PLayout'

CHAR_SEP_P2PLAYOUT = '.'  #P2PLayout模式中，sPairId与sSuffix之间的分隔符

#--------------------------------------
def testMain():
    pass

#--------------------------------------
if __name__=='__main__':
    testMain()
