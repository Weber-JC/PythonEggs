#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/3/21  WeiYanfeng
    封装 SNetHubRedis.py 针对Redis操作的封装

WeiYF.20160321 Redis键值设计(CmdStrArray采用 SerialCmdStrToString/SerialCmdStrFmString进行序列化):
0.约定如下：
    sServerIPPort=sServerIP:sServerPort #服务端守候的IP地址和端口号
    sClientIPPort=sClientIP:sClientPort #客户端连接上的IP地址和端口号
    由于Redis仅支持，RPOPLPUSH 而不支持 LPOPRPUSH，考虑将队列设计成LPUSH。
1.HASH_SNET_LINK_<sServerIPPort> 客户端连接状态，在线时才有该键值
    <sClientIPPort>_LoginInfo=登录时间(YYYY-MM-DD hh:nn:ss.zzz),<sInfo>
2.LIST_SNET_REQ_<sServerIPPort> 请求列表，
    将“sClientIPPort,命令标识,请求时间(毫秒级长整数)”插入到数组第0个位置，前缀取值空串
3.LIST_SNET_REP_<sServerIPPort> 应答列表
    将“sClientIPPort,命令标识,应答时间(毫秒级长整数)”插入到数组第0个位置，前缀取值空串
4.LIST_SNET_ING_<sServerIPPort> 处理列表，内容与 LIST_SNET_REQ_<sServerIPPort> 请求列表相同。

WeiYF.20160428~0429 优化键值设计:
0.设计目标：
    A.取消 HASH_SNET_LINK_<> 客户端链接状态设计
    B.取消 LIST_<>_<>_LOG 日志记录到Redis的设计
    C.基于已经测试出可以多个Worker进程同时处理请求，考虑将请求集中化、应答分离化，同时部署多个 SNetHubRedis
    D.同时考虑Woker进程要能够处理所有的请求，支持按 SNetHubRedis 配置区分请求队列
1.数据字典：
    sSNetHubIdStr=<sHostName4Param>:<sPort>
    sClientIPPort=<sClientIP>:<sClientPort>
    sUserIdString=客户端用户标识串，访问该用户可读标识串，唯一，有意义，类似于QQ号或者EMail
    pidHandle=处理进程的进程号
    sSubscribeScope=订阅范围串，由发布程序内部解释
    sKeyTail=请求或订阅键值后缀
2.请求应答过程设计：
    多个 SNetHubRedis 可以将请求推入同一个请求列表 LIST_SNET_REQUEST_<sKeyTail>，请求数据格式：
        将“<sSNetHubIdStr>,<sClientIPPort>,命令标识,请求时间串(YYYYMMDD-hhnnss.zzz)”插入到CmdIStr数组第0个位置
    多个工作进程可以同时从 LIST_SNET_REQUEST_<sKeyTail> 获得请求，RPOPLPUSH 到 LIST_SNET_DOING_<pidHandle> 队列进行处理
    工作进程处理结束后，将应答推入 LIST_SNET_REPLY_<sSNetHubIdStr> , 应答数据格式：
        将“<sClientIPPort>,命令标识,请求时间串(YYYYMMDD-hhnnss.zzz),应答时间串(YYYYMMDD-hhnnss.zzz)”插入到CmdOStr数组第0个位置
3.订阅发布过程设计：
    订阅时，在 HASH_SNET_SUBSCRIBE_<sKeyTail> 创建子键（取消订阅时，直接删除对应的子键）：
        子键键值是：<sUserIdString>
        子键取值是：<sClientIPPort>,订阅时间串(YYYYMMDD-hhnnss.xxx),<sSubscribeScope>
    为了方便后续程序试用，同时发布在 ROOM:HASH_SNET_SUBSCRIBE_<sKeyTail> 键值中。

"""
import os
from WyfPublicFuncs import PrintTimeMsg,GetCurrentTimeMSs, GetRedisClient, GetCriticalMsgLog

# from cmdstrFuncs import SaveCmdStrToArray,LoadCmdStrFmArray

from cmdstrSerial import SerialCmdStrToString, SerialCmdStrFmString


#--------------------------------------
class CRedisSNetFuncs:
    def __init__(self, sRedisParam, sKeyTail='', sLogFileName = __file__):
        self.sRedisParam = sRedisParam
        self.sKeyTail = sKeyTail
        self.sKEY_LIST_REQ = 'LIST_SNET_REQUEST_%s' % self.sKeyTail
        self.sKEY_HASH_SUB = 'HASH_SNET_SUBSCRIBE_%s' % self.sKeyTail

        self.cmLog = GetCriticalMsgLog('log@'+sLogFileName)
        self.oRedis = GetRedisClient(self.sRedisParam)

        # PrintTimeMsg("CRedisSNetFuncs.sKEY_LIST_REQ=(%s)..." % (self.sKEY_LIST_REQ))

    def __del__(self):
        if hasattr(self,'oRedis') and self.oRedis:
            self.oRedis.connection_pool.disconnect()
            PrintTimeMsg("CRedisSNetFuncs.disconnect()!!!")

    def WyfAppendToFile(self, sTagFN, sMsg):
        self.cmLog.log(sTagFN, sMsg)

    def clientSubscribeRequest(self, sClientIPPort, sUserIdString, sSubscribeScope):
        #客户端订阅请求
        sK = self.sKEY_HASH_SUB
        dictKV = {
            sUserIdString: '%s,%s,%s' % (sClientIPPort,GetCurrentTimeMSs(),sSubscribeScope),
        }
        self.oRedis.hmset(sK,dictKV)
        self.oRedis.publish('ROOM:'+sK, dictKV)

    def clientUnsubscribeRequest(self, sClientIPPort, sUserIdString):
        #客户端取消订阅请求
        sK = self.sKEY_HASH_SUB
        self.oRedis.hdel(sK,sUserIdString)
        dictKV = {
            sUserIdString: '%s,%s,%s' % (sClientIPPort,GetCurrentTimeMSs(),''), #空串表示删除
        }
        self.oRedis.publish('ROOM:'+sK, dictKV)


    def SNetCmdStrGetListLen(self,sRequestReply, sSNetHubIdStr):
        return self.oRedis.llen(self._getKeyListSnetCmd(sRequestReply, sSNetHubIdStr))

    def _getKeyListSnetCmd(self,sRequestReply, sSNetHubIdStr):
        sK = self.sKEY_LIST_REQ
        if sRequestReply=='Doing':
            sK = 'LIST_SNET_DOING_%s' % os.getpid()
        elif sRequestReply=='Reply':
            sK = 'LIST_SNET_REPLY_%s' % sSNetHubIdStr
        return sK

    def _snetCmdStrSaveToList(self, sRequestReply, sSNetHubIdStr, lsV):
        sV = SerialCmdStrToString(lsV)
        sK = self._getKeyListSnetCmd(sRequestReply,sSNetHubIdStr)
        oRet = self.oRedis.lpush(sK,sV)
        self.oRedis.publish('ROOM:'+sK, sV)
        return oRet

    def SNetCmdStrSaveToListRequest(self, sSNetHubIdStr, sClientIPPort, iCmdId, CmdStr):
        lsV = ['%s,%s,%s,%s' % (sSNetHubIdStr,sClientIPPort,iCmdId,GetCurrentTimeMSs())]
        lsV.extend(CmdStr)
        return self._snetCmdStrSaveToList('Request',sSNetHubIdStr, lsV)

    def SNetCmdStrSaveToListReply(self, sSNetHubIdStr, sClientIPPort, iCmdId, CmdStr):
        lsV = ['%s,%s,%s' % (sClientIPPort,iCmdId,GetCurrentTimeMSs())]
        lsV.extend(CmdStr)
        return self._snetCmdStrSaveToList('Reply',sSNetHubIdStr, lsV)

    def SNetCmdStrLoadFmListReply(self,sSNetHubIdStr):
        sV = self.oRedis.rpop(self._getKeyListSnetCmd('Reply',sSNetHubIdStr))
        # PrintTimeMsg("SNetCmdStrLoadFmList.sV=(%s)!" % sV)
        if sV:
            #lsV = LoadCmdStrFmArray(list(sV),0,len(sV))
            lsV = SerialCmdStrFmString(sV)
            # PrintTimeMsg("SNetCmdStrLoadFmList.lsV=(%s)!" % str(lsV))
            return lsV
        return []

    def SNetCmdStrDoOneCall(self,cbCallBack):
        #封装请求应答服务为调用，作为一种基本操作
        sKeyReq = self._getKeyListSnetCmd('Request','')
        sKeyIng = self._getKeyListSnetCmd('Doing','')
        sV = self.oRedis.rpoplpush(sKeyReq,sKeyIng)
        # PrintTimeMsg("SNetCmdStrLoadFmList.sV=(%s)!" % sV)
        if sV:
            #lsV = LoadCmdStrFmArray(list(sV),0,len(sV))
            lsV = SerialCmdStrFmString(sV)
            # PrintTimeMsg("SNetCmdStrDoOneCall.lsV=(%s)!" % str(lsV))
            cbCallBack(lsV)
            self.oRedis.lrem(sKeyIng,1,sV) #WeiYF.20160324 即便出现两个完全相同的请求，这里仅删除一个
            return True
        return False

    def PrintHintMsgForRequest(self,sHint):
        PrintTimeMsg("%s.WaitForRedis.KEY=(%s)..." % (sHint,self._getKeyListSnetCmd('Request','')))

    def PrintHintMsgForReply(self,sHint,sSNetHubIdStr):
        PrintTimeMsg("%s.WaitForRedis.KEY=(%s)..." % (sHint,self._getKeyListSnetCmd('Reply',sSNetHubIdStr)))

class CRedisSNetHubId(CRedisSNetFuncs):
    def __init__(self,sRedisParam, sSNetHubIdStr, sKeyTail='', sLogFileName = __file__):
        CRedisSNetFuncs.__init__(self,sRedisParam,sKeyTail,sLogFileName)
        self.sSNetHubIdStr = sSNetHubIdStr

    def SNetClientLogin(self, sClientIPPort, sUserIdString):
        sMsg = 'Login=%s,%s,%s' % (self.sSNetHubIdStr, sClientIPPort, sUserIdString)
        self.WyfAppendToFile('HubClientLog',sMsg)

    def SNetClientLogout(self, sClientIPPort, sUserIdString):
        sMsg = 'Logout=%s,%s,%s' % (self.sSNetHubIdStr, sClientIPPort, sUserIdString)
        self.WyfAppendToFile('HubClientLog',sMsg)
        if sUserIdString: #退出登录时，取消订阅
            self.clientUnsubscribeRequest(sClientIPPort, sUserIdString)

#--------------------------------------
def TestCRedisSNet():
    sRedisParam = '192.168.2.209:6379:10'
    sSNetHubIdStr = '127.0.0.1:8001'
    sClientIPPort = '127.0.0.1:34501'
    r = CRedisSNetFuncs(sRedisParam, '',__file__)
    print r.SNetCmdStrSaveToListRequest('sSNetHubIdStr',sClientIPPort,1001,['Test测试','Param\0A','Param、B','Param·C'])
    print r.SNetCmdStrGetListLen('Request','sSNetHubIdStr')#'Reply')


#--------------------------------------
if __name__ == '__main__':
    TestCRedisSNet()