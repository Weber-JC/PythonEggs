#!/usr/local/bin/python
#-*- coding:utf-8 -*-

"""
    2015/10/15  WeiYanfeng
    常用公共函数，都是需要导出的
"""

import time
import sys

reload(sys)
sys.setdefaultencoding('utf-8') #WeiYF.20150114 强制转为 utf-8 编码

def GetCurrentTime():
    return time.strftime("%Y%m%d-%H%M%S")

def GetUnixTimeStr(tmInt):
    return time.strftime("%Y%m%d-%H%M%S",time.gmtime(tmInt))

def GetUnixTimeLocal(tmInt):
    return time.strftime("%Y%m%d-%H%M%S",time.localtime(tmInt))

def GetLocalTime(iSeconds):
    return time.localtime(time.time()+iSeconds)

def GetYYYYMMDDhhnnss(iSeconds):
    return time.strftime("%Y%m%d-%H%M%S",time.localtime(time.time()+iSeconds))

def PrintInline(sMsg):
    try:
        sys.stdout.write(sMsg)
        sys.stdout.flush()
    except Exception, e:
        printHexString('UnicodeDecodeError=',sMsg)

def PrintNewline(sMsg):
    PrintInline('%s\n' % sMsg)

def PrintTimeMsg(sMsg):
    PrintInline("[%s]%s\n" % (GetCurrentTime(), sMsg))

def GetCurrentTimeMS(iTimeDiff=0):
    # return  '2015-05-19 18:22:55.681'
    # import datetime
    # # sTimeString = datetime.datetime.now() #2015-05-21 17:32:13.750000
    # sTimeString = str(datetime.datetime.fromtimestamp(time.time()+iTimeDiff))
    # # print "sTimeString=",sTimeString
    # return sTimeString[:-3] #保留到毫秒级
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def GetCurrentTimeMSs(iTimeDiff=0):
    # return  '2015-05-19 18:22:55.681'
    # import datetime
    # # sTimeString = datetime.datetime.now() #2015-05-21 17:32:13.750000
    # sTimeString = str(datetime.datetime.fromtimestamp(time.time()+iTimeDiff))
    # # print "sTimeString=",sTimeString
    # return sTimeString[:-3] #保留到毫秒级
    from datetime import datetime
    return datetime.now().strftime('%Y%m%d-%H%M%S.%f')[:-3]

def PrintMsTimeMsg(sMsg):
    import datetime
    PrintInline("[%s]%s\n" % (str(datetime.datetime.now())[:-3],sMsg))

def PrintAndSleep(sleepSeconds, sHint, bVerbose=True):
    if bVerbose:
        PrintTimeMsg("%s.sleep(%ss)..." % (sHint,sleepSeconds))
    time.sleep(sleepSeconds)

def GetTimeInteger():
    return int(time.time())

def GetTimeIntMS():
    return int(time.time()*1000)

def PrettyPrintObj(obj, sHint = ""):
    import pprint
    PrintInline(sHint)
    gPP = pprint.PrettyPrinter(indent=4)
    gPP.pprint(obj)
    sys.stdout.flush()

def PrettyPrintStr(obj):
    import pprint
    gPP = pprint.PrettyPrinter(indent=4)
    return gPP.pformat(obj)

def IsUtf8String(sStr):
    #判断一个串是否是 UTF-8 编码
    valid_utf8 = True
    try:
        sStr.decode('utf-8')
    except UnicodeDecodeError:
        valid_utf8 = False
    return valid_utf8

def printCmdString(sHint,CmdStr) : #采用列表来存储CmdStr入口参数
    CmdCnt = len(CmdStr)
    PrintNewline("[%s]%s.CmdCnt=%d={" % (GetCurrentTimeMS(),sHint,CmdCnt))
    for i in range(CmdCnt):
        try:
            sUTF = CmdStr[i]
            if not IsUtf8String(sUTF):
                sUTF = sUTF.decode('GBK').encode('UTF-8')
        except UnicodeDecodeError,e:
            # sUTF = CmdStr[i]
            pass
        PrintNewline("  CmdStr[%d].%d=%s=" % (i,len(CmdStr[i]),sUTF))
    PrintNewline("}")

def printHexString(sHint, arrayData):
    if arrayData==None: return
    PrintInline("%s=[\n" % (sHint))
    i = 0;
    for c in arrayData:
        PrintInline("%.2X " % (ord(c)))
        i += 1;
        if (i%16==0): PrintInline("\n")
    PrintInline("\n]\n")

def GetRandomInteger(iNum=8):
    # 生成十进制有 iNum 位的随机数
    import random
    return random.randint(pow(10,iNum-1), pow(10,iNum)-1) #sys.maxint/2

def ConvertStringToInt32(sString):
    sMD5 = md5(sString)
    sHex = sMD5[-8:]  # 4 bytes
    iInt = int(sHex, 16)
    return iInt

def GetSrcParentPath(srcfile):
    """
        取指定代码文件上级目录的绝对路径
    """
    import os
    import os.path
    if srcfile:
        sDir = os.path.dirname(os.path.realpath(srcfile))
        lsDir = sDir.split(os.sep)
        sDir = os.sep.join(lsDir[:-1])
        return sDir+os.sep
    else:
        print "Please use GetSrcParentPath(__file__)! Exit!"
        sys.exit(-1)

class GetCriticalMsgLog():
    #生成输出关键信息的对象
    def __init__(self, sPathParam='@.'):
        # 初始路径支持如下情况:
        #   1.依据代码文件 调用时传入 __file__ 计算出上一级路径
        #   2.使用当前工作路径；无需传入； 相当于 __file__ 取值为 . #os.getcwd()
        #   3.指定特定路径； 直接传入指定目录
        # 如果 sPathParam 中存在 @ 则表示是 __file__ 情况，@前面是路径转换后的子目录
        # 调用时传入 'log@'+__file__ 即可得到当前源码的上级目录
        iPos = sPathParam.find('@')
        if iPos<0:
            self.sLogPath = sPathParam
        else:
            self.sLogPath = GetSrcParentPath(sPathParam[iPos+1:])+sPathParam[0:iPos]
        PrintTimeMsg('GetCriticalMsgLog.sLogPath=%s=' % self.sLogPath)


    def log(self, sTagFN, sMsg):
        import os
        sFNameOut = self.sLogPath+os.sep+"wyf"+sTagFN+".log"
        with open(sFNameOut,"a") as f: #追加模式输出
            sS = "[%s]%s\n" % (GetCurrentTimeMSs(),sMsg)
            f.write(sS)

    def logFile(self, sMsg):
        #WeiYF.20151106 直接输出到指定文件
        sFNameOut = self.sLogPath
        with open(sFNameOut,"a") as f: #追加模式输出
            sS = "[%s]%s\n" % (GetCurrentTimeMSs(),sMsg)
            f.write(sS)

    def chkRename(self, sTagFN, iSizeMB, sBakTag='bak'):
        #将 sFileDir 目录下，大于 iSizeMB 的文件，重新命名为原文件名+当前日期形式。
        import os
        sDir = self.sLogPath+os.sep
        sFN = "wyf"+sTagFN+".log"
        sSrcDirFN = sDir+sFN
        iSizeInt = (1024*1024)*iSizeMB
        if os.path.getsize(sSrcDirFN)>iSizeInt:
            sBase, sExt = os.path.splitext(sFN)
            sOutFN = '%s_%s%s' % (sBase, GetCurrentTime(), sExt) #[0:8]
            try:
                #WeiYF.20160421 采用renames会自动创建子目录
                sOutDir = self.sLogPath+os.sep+sBakTag+os.sep
                os.renames(sSrcDirFN,sOutDir+sOutFN)
                PrintTimeMsg('rename(%s->%s)OK!' % (sSrcDirFN, sOutFN))
            except WindowsError:
                import traceback
                PrintTimeMsg(traceback.format_exc())

class CAppendLogBase:
    """
        WeiYF.20160512 新增基类，附带 WyfAppendToFile 成员函数
    """
    def __init__(self, sLogFileName, sLogSubDir = 'log'):
        self.cmLog = GetCriticalMsgLog(sLogSubDir+'@'+sLogFileName)

    def WyfAppendToFile(self, sTagFN, sMsg):
        self.cmLog.log(sTagFN, sMsg)


class ClassForAttachAttr:
    """
        WeiYF.20151029 为了更好设置保存动态属性，引入的类
    """
    def __init__(self):
        pass
#--------------------------------------

def Include(filename):
    """
        用于包含一些公共单元
    """
    if os.path.exists(filename):
        execfile(filename)

#-------------------------------------------------------
def GetCodeFmString(sStr, cSep=' '):
    # 从 "Code Value" 格式串中拆分出 Code 和 Value
    cv = sStr.split(cSep,1)
    if len(cv)>=2:
        return tuple(cv)
    return (sStr,'')

def crc32(str):
    import binascii
    return '%.8X' % (binascii.crc32(str) & 0xffffffff)

#--------------------------------------
def md5(str):
    import hashlib
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()

def md5file(fname):
    import hashlib
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()

# def HttpGet(sUrl):
#     import urllib2
#     return urllib2.urlopen(sUrl).read()

def HttpGet(sUrl,iTimeOut=60):
    import urllib2
    try:
        response = urllib2.urlopen(sUrl, timeout=iTimeOut)
        return response.read()
    except Exception,e:
        PrintTimeMsg('HttpGet.Exception=%s' % str(e))
        raise Exception(e) #WeiYF.20160222 继续触发该异常
    return ''
    # return urllib2.urlopen(sUrl,data=None, timeout=timeout).read()
    # return urllib2.urlopen(sUrl).read()

def HttpPostJson(sUrl,sData):
    import urllib2
    req = urllib2.Request(sUrl)
    req.add_header('Content-Type', 'application/json')
    req.add_header('encoding', 'utf-8')
    return urllib2.urlopen(req, sData).read()

def RequestsHttpGet(sUrl, jsonData={}, authTuple=(), timeout=60):
    import requests
    headers = {
        'content-type': 'application/json',
        'encoding': 'utf-8',
    }
    r = requests.get(sUrl, params=jsonData, auth=authTuple, timeout=timeout)
    return r.status_code, r.text #r.json()

def RequestsHttpPost(sUrl, jsonData, timeout=60):
    import requests
    headers = {
        'content-type': 'application/json',
        'encoding': 'utf-8',
    }
    r = requests.post(sUrl, data=jsonData, headers=headers, timeout=timeout)
    return r.status_code, r.text #r.json()

if __name__=="__main__":
    print '__file__',__file__
    print GetSrcParentPath('.')
    cmLog = GetCriticalMsgLog('log@'+__file__) #取源码文件目录
    # cmLog.log('Test','test')
    print GetCurrentTime()
    tmNow = time.time()
    print tmNow, GetUnixTimeLocal(tmNow)
    print "GetCurrentTimeMS()=",GetCurrentTimeMS(-10)
    s = u"\u7535\u8111-PC"
    print s
    PrintTimeMsg(s)
    PrintTimeMsg(s.decode('utf-8'))
    PrintTimeMsg(s.decode('utf-8').encode('utf-8'))