# -*- coding:utf-8 -*-
'''
Created on 2016-5-31
@author: Weber Juche

采用类似“纯虚函数”概念来定义 CSTP之Hub服务端 的回调接口基类。

;---------------------------
请求应答模式中，应答消息出口约定，CmdOStr[0] 取值为两个字母。
接收程序通过判断 CmdOStr[0][0]=='O' 来判断该指令执行成功与否。
#CmdOStr[n]成功出口:
0=OK                      ;OK=登录成功,
1+=sSuccessMsg            ;成功时附加消息
#CmdOStr[n]出错出口:
0=E<x>                    ;首字母E表示出错，第2字母x表示错误类型。
                          ;默认EE=普通错误(不区分),ES=系统错误(与应用逻辑的错误，由框架程序处理)
                          ;继续约定: EP=入口参数错误,ET=超时错误,
1=sErrorNo                ;错误代码，编码规则由应用自己定义。建议101+表示应用层面错误类型。
2=sErrorHintMsg           ;出错提示信息，可以展示给最终用户。
3=sErrorDebugMsg          ;出错调试信息，方便开发者调试。

;---------------------------
客户端登录指令接口描述如下：
[cstpLogin.CheckPasswd]
@=客户端检查密码登录
@@1=用于P2P模式下，客户端向服务端报告
@FN=CHubCallbackBase.py   ;源码所在文件名
@1N=1:1                   ;命令字类型;1:1/N
#CmdIStr[n]入口:
1=sAcctIdStr              ;客户端账号串
2=sEncPasswd              ;加密后密码
3=sDeviceInfo             ;客户端设备信息，可选
#CmdOStr[n]成功出口:
1=sAcctIdStr              ;客户端账号代码
2=sYMDhnsServer           ;服务端当前时间(YYYYMMDD-hhnnss)
3=sServerInfo             ;服务端附加信息，可选
;---------------------------

'''

from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep,ClassForAttachAttr
from cstpFuncs import CMDID_HREAT_BEAT,IsCmdNotify,GetCmdReplyFmRequest

class CHubCallbackBase:
    """
        CSTP之Hub服务端 的回调接口, 回调顺序如下：
        HandleServerStart 服务启动
            HandleClientBegin 客户端链接建立
            HandleCheckPasswd 检查客户端密码，替代Login
                HandleCheckReply 处理客户端发起的请求命令
                HandleCheckReply 检查需要返回客户端的应答数据，包括广播消息
            HandleClientEnd 客户端链接断开，也包括Logout
        HandleServerStop 服务停止
    """
    def __init__(self, sDiffKeyTail=''):
        self.sDiffKeyTail = sDiffKeyTail #用于Redis键值区分，默认是空串
        self.oBind = None # 监听等待的服务端对象
        # oBind 在非空情况下中有如下附加属性，在 HandleServerStart 中赋值：
        #     sSNetHubIdStr = 服务端标识串
        #     sServerIPPort = 服务端守护的IP地址端口号，冒号分隔
        #     iNowLinkNum = 当前客户端链接数
        #WeiYF.20160603 避免采用 oLink 来传递sClientIPPort，存在oLink=None的问题
        self.oLink = None # 新建立的客户端链接
        # oLink 在非空情况下中有如下附加属性，在 handleClientBegin 中赋值：
        #     iRequestCmdNum = 客户端请求计数
        #     iReplyCmdNum = 客户端应答计数
        self.iTestReplyCnt = 0
        self.bQuitLoopFlag = False  # 循环控制变量，由主控程序赋值
        pass

    def __del__(self):
        pass

    def SetCloseQuitFlag(self,sHint):
        # 设置退出标记
        self.bQuitLoopFlag = True

    def HandleServerStart(self, oBind):
        # 处理服务端启动事件
        self.oBind = oBind
        self.oBind.iNowLinkNum = 0
        PrintTimeMsg("HandleServerStart(%s,%s)..." % (
            self.oBind.sSNetHubIdStr, self.oBind.sServerIPPort))

    def HandleServerStop(self):
        # 处理服务端结束事件
        PrintTimeMsg("HandleServerStop(%s,%s)!!!" % (
            self.oBind.sSNetHubIdStr, self.oBind.sServerIPPort))
        self.oBind = None

    def HandleClientBegin(self, sClientIPPort):
        # 处理客户端开启事件
        self.oBind.iNowLinkNum += 1
        self.oLink = ClassForAttachAttr()
        self.oLink.iNotifyMsgNum = 0
        self.oLink.iRequestCmdNum = 0
        self.oLink.iReplyCmdNum = 0
        PrintTimeMsg("HandleClientBegin(%s).iNowLinkNum=%d=" % (
            sClientIPPort, self.oBind.iNowLinkNum))

    def HandleClientEnd(self, sClientIPPort):
        # 处理客户端结束事件
        self.oBind.iNowLinkNum -= 1
        PrintTimeMsg("HandleClientEnd(%s).iNowLinkNum=%d=" % (
            sClientIPPort, self.oBind.iNowLinkNum))

    def HandleNotifyMsg(self, sClientIPPort, CmdStr):
        # 处理客户端通知消息
        self.oLink.iNotifyMsgNum += 1
        PrintTimeMsg("HandleNotifyMsg.%s.Fm(%s)=%s=" % (
            self.oBind.sSNetHubIdStr, sClientIPPort, ','.join(CmdStr) ))

    def HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdStr):
        # 处理客户端请求命令
        self.oLink.iRequestCmdNum += 1
        PrintTimeMsg("HandleRequestCmd.%s.Fm(%s)=%s=" % (
            self.oBind.sSNetHubIdStr, sClientIPPort, ','.join(CmdStr) ))
        return True

    def HandleCheckReply(self):
        # 检查返回给客户端的应答消息（包括通知消息）等，返回格式为: (sClientIPPort,dwCmdId,CmdOStr)
        #   其中，返回 ('',0,[]) 表示没有数据要返回。sClientIPPort取值为*，表示是广播到所有客户端
        PrintAndSleep(1,'HandleCheckReply')
        if not self.oLink:
            return ('',0,[])
        else:
            self.iTestReplyCnt += 1
            if self.iTestReplyCnt%60==0:
                sClientIPPort = 'sClientIP:8888'
                dwCmdId = CMDID_HREAT_BEAT
                CmdOStr = ['HeartBeat','handleCheckReply.Test']
                #if hasattr(self.oLink,'iReplyCmdNum') #借助 hasattr 判断属性
                self.oLink.iReplyCmdNum += 1
                PrintTimeMsg("HandleCheckReply#%s=%s=" % (
                    self.oLink.iReplyCmdNum, ','.join(CmdOStr) ))
                return (sClientIPPort,dwCmdId,CmdOStr)
            else:
                return ('',0,[])

    def HandleCheckPasswd(self, sClientIPPort, dwCmdId, CmdIStr):
        # 处理客户端登录指令，返回格式为: (sClientIPPort,dwCmdId,CmdOStr)
        dictUserPass = {
            'testCSTP':'testCSTP',
        }
        CmdOStr = ['ES',   #0=系统错误，由框架断开链接
            '101',         #1=错误代码
            'sAcctIdStr or sEncPasswd error!', #2=错误提示信息
            'CHubCallbackBase.HandleCheckPasswd', #3=错误调试信息
        ]
        if dictUserPass.get(CmdIStr[1],'')==CmdIStr[2]:
            CmdOStr = ['OK',
                CmdIStr[1],       #1=sUserAcct,用户帐号
                GetCurrentTime(), #2=当前时间串
                'sServerInfo',    #3=服务端附加信息
            ]
        dwCmdId = GetCmdReplyFmRequest(dwCmdId)
        return (sClientIPPort,dwCmdId,CmdOStr)

#--------------------------------------
def testCHubCallbackBase():
    bhc = CHubCallbackBase() #oObj
    oBind = ClassForAttachAttr()
    oBind.sSNetHubIdStr = 'Test'
    oBind.sServerIPPort = 'sServerIP:8888'
    oBind.sHubIdString = 'sHubIdString'
    bhc.HandleServerStart(oBind)
    sClientIPPort = 'sClientIP:8888'
    bhc.HandleClientBegin(sClientIPPort)
    bhc.HandleClientEnd(sClientIPPort)
    bhc.HandleServerStop()

def testReturnTuple():
    def returnNone():
        return None
    (a,b,c) = returnNone() #此时会出异常
    print a,b,c

if __name__=='__main__':
    # testReturnTuple()
    testCHubCallbackBase()
