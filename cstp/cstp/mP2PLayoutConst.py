#!/usr/local/bin/python
#-*- coding:utf-8 -*-

"""
Created on 2016-7-1
@author: Weber Juche

    定义了 P2PLayout 模式中需要的一些常量
"""

# import sys
# from weberFuncs import PrintTimeMsg
#---------------------------------
# P2PLayout 模式中，内含命令：
# 由服务端发送系统消息；对于接收方来说，则是通知消息
CMD0_P2PLAYOUT_SEND_SYSTEM_MSG = '!P2PLayout.SendSystemMsg'
#  1=sAction       # PeerOnline=上线,PeerOffline=下线
#  2=sPairId
#  3=sSuffix
#  4=sOnlineList   #在线 sSuffix 列表串，逗号分隔
#  5+=其它参数

# 向同一sPairId中的其它Peer发命令请求；对于接收方来说，则是通知消息
CMD0_P2PLAYOUT_SEND_CMD_TOPEER = '!P2PLayout.SendCmdToPeer'
#  1=sSuffixFrom   # Peer消息源，框架程序检查调用方是否填入正确
#  2=sSuffixList   # 逗号分隔的 sSuffix；取值 * ，表示全部其它Peer； *=群发，@=择一
#  3+=其它参数      # WeiYF.20160705 @=择一 这种情况属于负载均衡应用中需要的，这里暂不支持。

#--------------------------------------
# def GetTextPeerIdForP2PLayout(sPairId, sSuffix):
#     return '%s.%s' % (sPairId, sSuffix)

#--------------------------------------
def testMain():
    pass

#--------------------------------------
if __name__=='__main__':
    testMain()
