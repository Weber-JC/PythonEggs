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
; 2016-7-1 鉴权类型sP2PKind对应的P2P相关概念，解释如下：
一、典型意义上P2P模式，命名为 P2PCommon 。指的是 sPeerId 是由Peer自己向服务端注册生成的，
Peer自己创建好友关系，然后好友之间就可以直接交互，或者通过群组交互。

二、预分配的P2P模式，命名为 P2PLayout 。 指的是 sPeerId不需要Peer自主注册，需要后台管理方
提前分配 sPairId 和 sSuffix 给Peer，服务端根据sPairId和sSuffix来计算生成sPeerId。
客户端之间是通过 <sSuffix> 相互访问的，不同PairId之间隔绝访问。
sPeerId是计算出来的,仅用于服务端内部查找定位出客户端链接。
    服务端部署需要填入 sHubId, 允许接入的 sPairId 列表（可能存放在数据库中）。
    客户端部署需要填入 sHubId, sPairId, sAcctPwd 和 sSuffix 。
sPairId和sSuffix 编码规则：
    一般要求是字母和数字组合，区分大小写；可以有
    但不可以有如下字符: ~!@#$%^&*()`{}|\ ，但可以有 :;,.+-_

三、共享账号模式，命名为 AcctShare 。指的是在客户端共享账号登录，适用于传统的客户端/服务器模式。
此时服务端的主要工作之将处理客户端的请求并返回应答。不像P2P那样，会在不同客户端之间进行交互。

;---------------------------

客户端登录指令接口描述如下：
[<cstpFuncs.CMD0_CHECK_AUTH>]
@=客户端接入鉴权，同时完成P2P登录。
@1N=1:1                   ;命令字类型;1:1/N
#CmdIStr[n]入口:
1=sP2PKind                ;鉴权类型，取值如下（定义在 mGlobalConst.py 中）：
                          ;     AcctShare=客户端可共享同一个账号鉴权，
                          ;         这种模式不检查 sHubId 是否匹配；而且 ynForceLogin 参数无效；
                          ;     P2PCommon=典型P2P模式，客户端使用自己注册的sPeerId
                          ;         sAcctNo=sPeerId 是提前申请获得的唯一标识
                          ;         sAcctPwd=是提前申请时自定义的访问密码；可修改
                          ;     P2PLayout=预分配P2P模式
                          ;         sAcctNo=sPairId:sSuffix 之间采用英文点号(.)分隔。
                          ;             其中 sPairId 是提前分配的唯一标识
                          ;             其中 sSuffix 是互相间访问后缀标识
                          ;         sAcctPwd=是提前分配的访问密码；可提供修改服务
2=sHubId                  ;服务端标识串；用于客户端识别服务端，避免连错服务器；默认为 @HubId
3=sAcctId                 ;客户端账号标识
4=sAcctPwd                ;客户端账号密码;
5=ynForceLogin            ;YN是否强制登录; N=非强制登录，若检测出对应账号已登录，则返回错误；
                          ;               Y=强制登录，若检测出对应账号已登录，则踢其下线。
6=sClientInfo             ;客户端设备信息，可选
#CmdOStr[n]成功出口
1=sP2PKind                ;鉴权类型
2=sHubId                  ;服务端标识串
3=sAcctId                 ;客户端账号标识
4=sYMDhnsServer           ;服务端当前时间(YYYYMMDD-hhnnss)
5=sServerInfo             ;服务端附加信息，可选
;---------------------------

'''

from weberFuncs import GetCurrentTime,PrintTimeMsg,PrintAndSleep,ClassForAttachAttr
from cstpFuncs import CMDID_HREAT_BEAT, IsCmdNotify,GetCmdReplyFmRequest
from mGlobalConst import P2PKIND_ACCTSHARE

from cstpErrorFuncs import CSTPError,GenErrorTuple

class CHubCallbackBasicBase:
    """
        CSTP之Hub服务端 的回调接口, 回调顺序如下：
        HandleServerStart 服务启动
            HandleClientBegin 客户端链接建立
            HandleCheckAuth 客户端鉴权，Login
                HandleCheckReply 处理客户端发起的请求命令
                HandleCheckReply 检查需要返回客户端的应答数据，包括广播消息
            HandleClientEnd 客户端链接断开，也包括Logout
        HandleServerStop 服务停止
    """
    def __init__(self,sHubId):
        self.sHubId = sHubId
        self.oBind = None # 监听等待的服务端对象
        # oBind 在 HandleServerStart 中赋值：
        #     oHub = TCmdStringHub服务框架对象标识，可以从中读取一些全局参数
        #   在非空情况下中有如下附加属性：
        #     iNowLinkNum = 当前客户端链接数
        #WeiYF.20160623 使用GetBindAttrValue和GetLinkAttrValue两个函数来获取动态附加属性
        #WeiYF.20160627 以 sClientIPPort 为键值创建一个字典，来保管 oLink 信息。
        self.dictObjLinkByCIP = {}
        # oLink 在 handleClientBegin 中赋值：
        #     sClientIPPort = 客户端的IP地址端口号，冒号分隔
        #   在P2P11模式下，还有
        #     sPeerId = Peer标识
        #     sPairId = Pair标识
        #     sSuffix = Pair后缀
        #   在非空情况下中有如下附加属性：
        #     iRequestCmdNum = 客户端请求计数
        #     iReplyCmdNum = 客户端应答计数
        self.iTestReplyCnt = 0
        self.bQuitLoopFlag = False  # 循环控制变量，由主控程序赋值
        self.sSelfHubId = ''

    def __del__(self):
        pass

    def SetCloseQuitFlag(self,sHint):
        # 设置退出标记
        self.bQuitLoopFlag = True

    def GetHubAttrValue(self, sAttrName, sDefValue=''):
        # 根据属性名称，从 oBind.oHub 读取相关属性取值
        if sDefValue=='@':
            sDefValue = '@No %s' % sAttrName
        if self.oBind==None: return sDefValue
        if not hasattr(self.oBind,'oHub'): return sDefValue
        return getattr(self.oBind.oHub,sAttrName,sDefValue)

    def GetLinkAttrValue(self, sClientIPPort, sAttrName, sDefValue=''):
        # 根据属性名称，从 oLink 读取相关属性取值
        oLink = self.dictObjLinkByCIP.get(sClientIPPort,None)
        if sDefValue=='@':
            sDefValue = '@No %s' % sAttrName
        if oLink==None: return sDefValue
        return getattr(oLink,sAttrName,sDefValue)

    def HandleServerStart(self, oHub):
        # 处理服务端启动事件
        self.oBind = ClassForAttachAttr()
        self.oBind.oHub = oHub
        self.oBind.iNowLinkNum = 0
        PrintTimeMsg("HandleServerStart(%s,%s)..." % (
            self.sHubId, self.GetHubAttrValue('sServerIPPort','@')))

    def HandleServerStop(self):
        # 处理服务端结束事件
        PrintTimeMsg("HandleServerStop(%s,%s)!!!" % (
            self.sHubId, self.GetHubAttrValue('sServerIPPort','@')))
        self.oBind = None

    def HandleClientBegin(self, sClientIPPort):
        # 处理客户端开启事件
        self.oBind.iNowLinkNum += 1
        oLink = ClassForAttachAttr()
        oLink.sClientIPPort = sClientIPPort
        oLink.iNotifyMsgNum = 0
        oLink.iRequestCmdNum = 0
        oLink.iReplyCmdNum = 0
        self.dictObjLinkByCIP[sClientIPPort] = oLink
        #WeiYF.20160627 暂时不考虑 sClientIPPort 重复问题
        PrintTimeMsg("HandleClientBegin(%s).iNowLinkNum=%d=" % (
            sClientIPPort, self.oBind.iNowLinkNum))

    def HandleClientEnd(self, sClientIPPort):
        # 处理客户端结束事件
        self.oBind.iNowLinkNum -= 1
        del self.dictObjLinkByCIP[sClientIPPort]
        # delattr(self.oLink,'sClientIPPort')
        PrintTimeMsg("HandleClientEnd(%s).iNowLinkNum=%d=" % (
            sClientIPPort, self.oBind.iNowLinkNum))

    def HandleNotifyMsg(self, sClientIPPort, CmdIStr):
        # 处理客户端通知消息，返回bDone=True表示已处理，bDone=False表示未处理
        oLink = self.dictObjLinkByCIP.get(sClientIPPort,None)
        if oLink:
            oLink.iNotifyMsgNum += 1
            PrintTimeMsg("HandleNotifyMsg.Fm(%s)=%s=" % (sClientIPPort, ','.join(CmdIStr) ))
            return False
        else:
            PrintTimeMsg("HandleNotifyMsg.Fm(%s).oLink=%s=" % (sClientIPPort, str(oLink) ))
            return True

    def HandleRequestCmd(self, sClientIPPort, dwCmdId, CmdIStr):
        # 处理客户端请求命令，返回bDone=True表示已处理，bDone=False表示未处理
        oLink = self.dictObjLinkByCIP.get(sClientIPPort,None)
        if oLink:
            oLink.iRequestCmdNum += 1
            PrintTimeMsg("HandleRequestCmd.Fm(%s)=%s=" % (sClientIPPort, ','.join(CmdIStr) ))
            return False
        else:
            PrintTimeMsg("HandleRequestCmd.Fm(%s).oLink=%s=" % (sClientIPPort, str(oLink) ))
            return True

    def HandleCheckAuth(self, sClientIPPort, dwCmdId, CmdIStr):
        # 处理客户端鉴权，返回格式为: (sClientIPPort,dwCmdId,CmdOStr)
        # PrintTimeMsg("HandleCheckAuth.dwCmdId=%d=" % dwCmdId)
        sP2PKind = CmdIStr[1]
        sHubId = CmdIStr[2]
        sAcctId = CmdIStr[3]
        sAcctPwd = CmdIStr[4]
        ynForceLogin = CmdIStr[5]
        sClientInfo = CmdIStr[6]
        if sP2PKind!=P2PKIND_ACCTSHARE and sHubId!=self.sHubId:
            CmdOStr = GenErrorTuple(CSTPError.CHECK_AUTH_HUBID,'CHubCallbackBase.HandleCheckAuth',
                                    sP2PKind=sP2PKind, sHubId=sHubId)
        else:
            oLink = self.dictObjLinkByCIP.get(sClientIPPort,None)
            if oLink:
                CmdOStr = self.DoHandleCheckAuth(oLink, dwCmdId,sHubId,
                                sP2PKind, sAcctId, sAcctPwd, ynForceLogin, sClientInfo)
            else:
                CmdOStr = GenErrorTuple(CSTPError.CHECK_AUTH_NO_CIP,'CHubCallbackBase.HandleCheckAuth',
                                    sClientIPPort=sClientIPPort)
        return (sClientIPPort,GetCmdReplyFmRequest(dwCmdId),CmdOStr)

    def DoHandleCheckAuth(self, oLink, dwCmdId, sHubId,
                            sP2PKind, sAcctId, sAcctPwd, ynForceLogin, sClientInfo):
        # 处理客户端鉴权，返回格式为: CmdOStr
        return GenErrorTuple(CSTPError.CHECK_AUTH_P2PKIND,'CHubCallbackBase.DoHandleCheckAuth',
                             sP2PKind=sP2PKind)

    def HandleCheckAllLinkReply(self):
        # 检查所有链接的应答返还消息（包括通知消息）等，返回格式为: (sClientIPPort,dwCmdId,CmdOStr)
        #   其中，返回 ('',0,[]) 表示没有数据要返回。sClientIPPort取值为*，表示是广播到所有客户端
        (sClientIPPort,dwCmdId,CmdOStr) = self.DoHandleCheckAllLinkReply()
        if sClientIPPort:
            oLink = self.dictObjLinkByCIP.get(sClientIPPort,None)
            if oLink:
                oLink.iReplyCmdNum += 1  #self.GetHubAttrValue('sHubId','@')
                PrintTimeMsg("HandleCheckAllLinkReply.Fm(%s).iReplyCmdNum=%s=" % (sClientIPPort, oLink.iReplyCmdNum ))
        return (sClientIPPort,dwCmdId,CmdOStr)

    def DoHandleCheckAllLinkReply(self):
        # 处理检查所有链接的应答返还消息（包括通知消息）等，返回接口与 HandleCheckAllLinkReply 一致
        return ('',0,[])


#--------------------------------------
def testCHubCallbackBasicBase():
    bhc = CHubCallbackBasicBase('sHubId') #oObj
    oBind = ClassForAttachAttr()
    bhc.HandleServerStart(oBind)
    print 0, bhc.GetLinkAttrValue('sClientIPPort')
    sClientIPPort = 'sClientIP:8888'
    bhc.HandleClientBegin(sClientIPPort)
    print 1, bhc.GetLinkAttrValue('sClientIPPort')
    bhc.HandleClientEnd(sClientIPPort)
    print 2, bhc.GetLinkAttrValue('sClientIPPort')
    bhc.HandleServerStop()

def testReturnTuple():
    def returnNone():
        return None
    (a,b,c) = returnNone() #此时会出异常
    print a,b,c

if __name__=='__main__':
    # testReturnTuple()
    testCHubCallbackBasicBase()
