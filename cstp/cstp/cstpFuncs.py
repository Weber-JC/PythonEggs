#!/usr/local/bin/python
#-*- coding:utf-8 -*-

"""
Created on 2016-5-30
@author: Weber Juche

    提供了 CSTP 需要一些公共函数，如序列化、CmdId计算等。
"""

import sys
from weberFuncs import PrintTimeMsg,printHexString,printCmdString,IsUtf8String

CMDID_HREAT_BEAT = 0x80000000 #心跳包取值
CMDID_NOTIFY_MSG = 0          #通知消息

CMD0_CHECK_AUTH = '!CSTP.CheckAuth' # 检查接入授权命令字
CMD0_ECHO_CMD = '!CSTP.EchoCmd' # 接入框架回声命令字，能则实现

# P2P11模式中，内含命令：
CMD0_P2P11_SEND_SYSTEM_MSG = '!P2P11.SendSystemMsg' # 发送系统消息
#  1=sAction       # PeerOnline=上线,PeerOffline=下线
#  2=sPairId
#  3=sSuffix
#  4=sOnlineList   #在线 sSuffix 列表串，逗号分隔
#  5+=其它参数

CMD0_P2P11_SEND_CMD_TOPEER = '!P2P11.SendCmdToPeer' # 向同一sPairId中的其它Peer发命令请求
#  1=sSuffixFrom   # Peer消息源，由框架程序插入
#  2=sSuffixList   # 逗号分隔的 sSuffix；取值 * ，表示全部其它Peer
#  3+=其它参数


#--------------------------------------
# 提供 CmdId 相关计算函数
def Int8ToHex(dwInt):
    """ 将双字无符号整数转为8字节16进制串 """
    sS = '%.8X' % dwInt
    return sS

def HexToInt8(sHex):
    """ 将8字节16进制串转为双字无符号整数 """
    try:
        return int(sHex,16)
    except Exception, e:
        PrintTimeMsg('HexToInt8(%s)=Error' % sHex)
        raise

def IsHeartBeat(dwCmdId):
    """ 是否是心跳包 """
    global CMDID_HREAT_BEAT
    return dwCmdId==CMDID_HREAT_BEAT

def IsCmdNotify(dwCmdId):
    """ 是否是广播通知消息，无需应答 """
    return dwCmdId==CMDID_NOTIFY_MSG

def IsCmdRequest(dwCmdId):
    """ 是否是请求命令 """
    global CMDID_HREAT_BEAT
    return 0<dwCmdId<CMDID_HREAT_BEAT

def IsCmdReply(dwCmdId):
    """ 是否是应答命令 """
    global CMDID_HREAT_BEAT
    return CMDID_HREAT_BEAT<dwCmdId

def GetCmdType(dwCmdId):
    if IsCmdReply(dwCmdId): return 'Reply'
    if IsCmdNotify(dwCmdId): return 'Notify'
    if IsCmdRequest(dwCmdId): return 'Request'
    return 'HeartBeat'

def GetCmdReplyFmRequest(dwCmdId):
    """ 从请求命令转换得到应答命令，返回0表示失败 """
    global CMDID_HREAT_BEAT
    if IsCmdRequest(dwCmdId):
        return dwCmdId+CMDID_HREAT_BEAT
    else:
        PrintTimeMsg('GetCmdReplyFmRequest.dwCmdId=%.8X,Error' % dwCmdId)
        return 0

def GetCmdRequestFmReply(dwCmdId):
    """ 从应答命令转换得到请求命令，返回0表示失败 """
    global CMDID_HREAT_BEAT
    if IsCmdReply(dwCmdId):
        return dwCmdId-CMDID_HREAT_BEAT
    else:
        PrintTimeMsg('GetCmdRequestFmReply.dwCmdId=%.8X,Error' % dwCmdId)
        return 0

gdwReqCmdIdNext=1 #下一个有效的CmdId，
def GenNewReqCmdId():
    """ 生成新的请求命令标识 """
    global gdwReqCmdIdNext
    iCmdId = 1
    if IsCmdRequest(gdwReqCmdIdNext):
        iCmdId = gdwReqCmdIdNext
        gdwReqCmdIdNext += 1
    else:
        gdwReqCmdIdNext = iCmdId
    return iCmdId

def testCmdId():
    print Int8ToHex(0x00008000)
    print Int8ToHex(0x80000000)
    print Int8ToHex(0x8FFFFFFF)
    print Int8ToHex(0xFFFFFFFF)
    print Int8ToHex(HexToInt8('8FFFFFFF'))
    print '-'*8
    print IsHeartBeat(0)
    print IsHeartBeat(0x80000000)
    print IsCmdNotify(0)
    print '-'*8
    print IsCmdRequest(0)
    print IsCmdRequest(1)
    print IsCmdRequest(0x80000000)
    print IsCmdRequest(0x08000000)
    print '-'*8
    print IsCmdReply(0)
    print IsCmdReply(0x80000000)
    print IsCmdReply(0x80000001)
    print IsCmdReply(0x08000000)
    print '-'*8
    print Int8ToHex(GetCmdReplyFmRequest(1234))
    print Int8ToHex(GetCmdReplyFmRequest(0x80000001))
    print '-'*8
    print Int8ToHex(GetCmdRequestFmReply(1234))
    print Int8ToHex(GetCmdRequestFmReply(0x80000123))
    print '-'*8
    print Int8ToHex(GenNewReqCmdId())
    print Int8ToHex(GenNewReqCmdId())
    print Int8ToHex(GenNewReqCmdId())

#--------------------------------------
# 序列化函数
"""
WeiYF.20160426 超长串后追加串，会使xxxLV序列化挂掉。
问题出在：采用两字节的16进制来保存长度；而长度一旦超过256,则转为0,但限定只能是最后一个串。
改进办法：将长度转为10进制逗号分隔串，采用分号分隔放在序列串头。后续依次是各个串内容。
"""

def SerialCmdStrToString(CmdStr):
    # 序列化CmdStr到字符串
    sRetLen = ''
    sRetData = ''
    listCmdStr = list(CmdStr)
    for cs in listCmdStr:
        # sRetLen += '%d,' % len(cs)
        if not IsUtf8String(cs):
            cs = cs.decode('GBK').encode('utf-8') #统一采用utf8编码，避免unicode长度问题
        cs = bytes(cs) #WeiYF.20160601 转为字节数组，避免编码造成的长度影响
        sRetLen += '%d,' % len(cs)
        sRetData += cs
    if sRetLen: sRetLen = sRetLen[:-1] # remove tail comma
    return '%s;%s' % (sRetLen,sRetData)

def SerialCmdStrFmString(sData):
    # 从字符串反序列化到CmdStr
    lsCmdStr = []
    lsPart = sData.partition(';')
    if not lsPart[1]:
        PrintTimeMsg('SerialCmdStrFmString.sData=%s,no Semicolon!' % (sData))
        return lsCmdStr
    lenStr = lsPart[0]
    strData = lsPart[2]
    lsLen = []
    for sLen in lenStr.split(','):
        if sLen:
            try:
                lsLen.append(int(sLen))
            except ValueError:
                PrintTimeMsg('SerialCmdStrFmString.lenStr=%s=Error!' % (lenStr))
                return lsCmdStr
    pB = 0
    for iLen in lsLen:
        sCS = strData[pB:pB+iLen]
        # sCS = sCS.decode('utf-8')
        lsCmdStr.append(sCS)
        pB += iLen
    return lsCmdStr

def PrintTestSerialCmdStr(lsCmdStr):
    sData = SerialCmdStrToString(lsCmdStr)
    PrintTimeMsg('SerialCmdStrToString.sData=%s=' % sData)
    # # printHexString('SerialCmdStrToString',sData)
    CmdStr = SerialCmdStrFmString(sData)
    printCmdString("SerialCmdStrFmString",CmdStr)


def testSerialCmdStr():
    # PrintTestSerialCmdStr(['1A','2BC','3test','4测试一下test汉字'])
    # return
    lsCmdStr = ['000', 'OK',
                '{"ltc": {"XINA50": "0", "totalassets": 299.9034, "marginaccount": "149.9034", "XINA50_orderNum": 1, "netassets": 299.9034, "fltc": "149.9034", "unmatched": 0, "XINA50_frozen": 0, "mainwallet": "150", "fltc_frozen": 0}, "usd": {"marginaccount": 908.79, "BTC2USD_frozen": 913.07, "netassets": 1821.86, "BTC2USD": 908.79, "BTC2USD_orderNum": 5, "totalassets": 1821.86}, "flags": {"XINA50": "0", "GBPUSD": "0", "XAUUSD": "0", "EURUSD": "0", "AUDUSD": "0", "WEEKLYFUTURES": "0", "DAXEUR": "0", "USDJPY": "0", "USDCNH": "0", "XTIUSD": "0", "DAOUSD": "0", "XAGUSD": "0"}, "btc": {"GBPUSD": "1.18", "BTC2USD": "15.21338", "NK225M_orderNum": 0, "XINA50_frozen": 0.2, "XAUUSD_frozen": 0, "AUDUSD_frozen": 0, "XAGUSD_orderNum": 0, "XINA50_orderNum": 0, "DAOUSD_frozen": 0.1, "XAGUSD": "2.93", "unmatched": 1.03, "EURUSD": "1.914", "XTIUSD_frozen": 0.1, "totalassets": 232.72683575, "DAOUSD_orderNum": 0, "GBPUSD_frozen": 0, "XTIUSD_orderNum": 0, "stock_frozen": "0", "XAGUSD_frozen": 0, "marginaccount": "104.89169575", "DAXEUR_orderNum": 0, "XAUUSD": "6.1436", "USDCNH_frozen": 0.1, "BTC2USD_orderNum": 1, "AUDUSD": "12.9503", "NK225M_frozen": 0.1, "DAXEUR": "19.272036", "mainwallet": "126.80514", "fbtc_frozen": 0, "XAUUSD_orderNum": 0, "USDCNH": "1.9316", "EURUSD_orderNum": 0, "USDCNH_orderNum": 0, "EURUSD_frozen": 0, "AUDUSD_orderNum": 0, "XINA50": "16.22941778", "BTC2USD_frozen": 0.33, "netassets": 232.72683575, "NK225M": "3.40699", "fbtc": "0.3", "USDJPY_frozen": 0, "DAXEUR_frozen": 0.1, "USDJPY": "4.9617", "GBPUSD_orderNum": 0, "USDJPY_orderNum": 0, "XTIUSD": "8.0554", "DAOUSD": "10.40327197"}}',
    #] #'2016-04-26 11:48:25.282']
    '2016-04-26 11:48:25.282']
    PrintTestSerialCmdStr(lsCmdStr)

#--------------------------------------
def SerialCstpHeadToString(dwCmdId, dwDataLen):
    # 序列化出 CSTP 包头
    return Int8ToHex(dwCmdId)+Int8ToHex(dwDataLen)

def SerialCstpHeadFmString(sHexHead16):
    # 从 CSTP 包头反序列化
    dwCmdId = HexToInt8(sHexHead16[0:8])
    dwDataLen = HexToInt8(sHexHead16[9:16])
    return (dwCmdId,dwDataLen)

def testSerialCstpHead():
    sT = SerialCstpHeadToString(0x1234, 0x56)
    print sT
    (dwCmdId,dwDataLen) = SerialCstpHeadFmString(sT)
    print Int8ToHex(dwCmdId),Int8ToHex(dwDataLen)

#--------------------------------------
def SerialCstCmdStrToString(dwCmdId,CmdStr,bPrint):
    # 序列化CSTP CmdStr到字符串
    if bPrint:
        printCmdString("SerialCstCmdStrToString.dwCmdId=%d" % dwCmdId,CmdStr)

    sData = SerialCmdStrToString(CmdStr)
    dwDataLen = len(sData)
    sHead = SerialCstpHeadToString(dwCmdId,dwDataLen)
    return sHead+sData

def SerialCstCmdStrFmString(sData):
    # 反序列化出CSTP 包头和CmdStr
    (dwCmdId,dwDataLen) = SerialCstpHeadFmString(sData[0:16])
    CmdStr = SerialCmdStrFmString(sData[16:16+dwDataLen])
    return (dwCmdId,CmdStr)

def testSerialCstCmdStr():
    sGBK = u"国标汉字".decode('utf-8').encode('GBK')
    sT = SerialCstCmdStrToString(0x1234, ['test','123','456',u'test汉字123',sGBK,u"国标汉字"],True)
    print sT
    (dwCmdId,CmdStr) = SerialCstCmdStrFmString(sT)
    print Int8ToHex(dwCmdId),CmdStr
    printCmdString("test=",CmdStr)

#--------------------------------------
def GetTextPeerIdForP2P11(sPairId, sSuffix):
    return '%s.%s' % (sPairId, sSuffix)
#--------------------------------------
def testBytes():
    s = '1234测试test'
    print s,len(s)
    b = bytes(s)
    print b,len(b)

#--------------------------------------
if __name__=='__main__':
    testBytes()
    # testSerialCmdStr()
    # testCmdId()
    # testSerialCstpHead()
    testSerialCstCmdStr()
