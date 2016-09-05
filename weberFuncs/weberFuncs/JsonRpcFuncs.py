#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
    2015/10/19  WeiYanfeng
    将 JSONRPC 相关的函数放在这里
"""
import sys
from WyfPublicFuncs import PrintTimeMsg,PrettyPrintStr,GetCodeFmString,\
    PrintMsTimeMsg,GetCurrentTimeMS

def GetJsonRpcClient(sJsonRpcHostPort,sJsonRpcUserPass):
    import pyjsonrpc
    lsUP = sJsonRpcUserPass.split(':')
    if len(lsUP)<2:
        return None
    #PrintMsTimeMsg("GetJsonRpcClient(%s)..." % sJsonRpcHostPort)
    oRet = pyjsonrpc.HttpClient(
            url = "http://%s/" % sJsonRpcHostPort,
            username = lsUP[0],
            password = lsUP[1],
            #timeout = 60,  #Specifies a timeout in seconds for blocking operations
        )
    PrintMsTimeMsg("GetJsonRpcClient.oRet=(%s)..." % oRet)
    return oRet


def LoopRunJsonRpcServer(sHostPort, sServSeq, ReqHandlerClass):
    import pyjsonrpc
    PrintTimeMsg('LoopRunJsonRpcServer.sHostPort=(%s),sServSeq=(%s)...' % (
                sHostPort,sServSeq))
    lsHP = sHostPort.split(':')
    if len(lsHP)<2:
        PrintTimeMsg("hpHostPort=(%s)Error,should (IP:PORT)fmt! EXIT!" % hpHostPort)
        sys.exit(-101)
        return
    # Threading HTTP-Server
    http_server = pyjsonrpc.ThreadingHttpServer(
        server_address = (lsHP[0], int(lsHP[1])),
        RequestHandlerClass = ReqHandlerClass
    )
    PrintTimeMsg('Start JsonRpcServer http://%s ...' % (sHostPort))
    try:
        http_server.serve_forever(poll_interval=0.01)
    except KeyboardInterrupt:
        http_server.shutdown()
    PrintTimeMsg('Stop JsonRpcServer http://%s !!!' % (sHostPort))

def LoopRunRpcServer(sCallType, sHostPort, sServSeq, sPythonDir=''):
    """
        启动远程服务，支持如下两种协议形式
        :param sCallType: JsonRPC/ZmqRPC
        :param sHostPort: 服务守护的IP和PORT
        :param sServSeq: 服务序号标识串
        :param sPythonDir: CmdHandle 脚本所在路径，要带上最后的路径分隔符
        :return: 无
    """
    lsServ = sServSeq.split('.')
    if len(lsServ)<2:
        PrintTimeMsg("LoopRunRpcServer.sServSeq=(%s)Error,EXIT!" % (sServSeq))
        sys.exit(-1)
    lsHP = sHostPort.split(':')
    if len(lsHP)<2:
        PrintTimeMsg("LoopRunRpcServer.sHostPort=(%s)Error,EXIT!" % (sHostPort))
        sys.exit(-1)
    sHost = lsHP[0]
    if sHost!='127.0.0.1': #WeiYF.20151026 非127.0.0.1则是0.0.0.0
        sHost = '0.0.0.0'
    sHostPort = '%s:%s' % (sHost,lsHP[1])
    if sCallType[:1]=='Z':# JsonRPC/ZmqRPC
        from WyfZmqCmdFuncs import LoopRunExecZmqCmdReply
        LoopRunExecZmqCmdReply(sHostPort, sServSeq, sPythonDir)
    else:
        # from WyfPublicFuncs import importModuleClass,LoopRunExecJsonRpcServer
        CmdHandleStandard = importModuleClass(sPythonDir+'CmdHandle'+lsServ[0],'CmdHandleStandard')
        m = CmdHandleStandard( [sServSeq] )
        setattr(m,'sServ',lsServ[0])
        LoopRunJsonRpcServer(sHostPort, sServSeq, GenJsonRpcReqHandlerClass(m))

#--------------------------------------
def GenJsonRpcReqHandlerClass(oCmdHandleStandard):
    import pyjsonrpc
    class RequestHandlerCmdClass(pyjsonrpc.HttpRequestHandler):
        """
            CallCmd 形式的类封装
        """
        @pyjsonrpc.rpcmethod
        def CallCmd(self, sServ, sFuncName, lsParam):
            #WeiYF.20151020 调用时直接给出函数名，无需添加服务前缀；加了反而不行
            # PrintTimeMsg("CallCmd.sServ=(%s)!" % (sServ)) #通过参数直接传入了
            # WeiYF.20151022 通过如下方法也可以取到对象的附加属性
            # sServAttr = ''
            # if hasattr(oCmdHandleStandard,'sServ'): sServAttr = oCmdHandleStandard.sServ
            # PrintTimeMsg("CallCmd.sServAttr=(%s)!" % (sServAttr))
            CmdIStr = [sServ+'.'+sFuncName]
            CmdIStr.extend(lsParam)
            # PrintTimeMsg('CallCmd(%s,%s)...' % (sFuncName, CmdIStr))
            try:
                PrintMsTimeMsg("CallByName(%s)..." % sFuncName)
                oRet = oCmdHandleStandard.CallByName(sFuncName,CmdIStr)
                PrintMsTimeMsg("CallByName(%s)!!!" % sFuncName)
            except Exception, e:
                import traceback
                traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
                PrintTimeMsg('CallCmd.Exception.e=(%s)' % (str(e)))
            # PrintTimeMsg('CallCmd(%s,%s)=%s' % (sFuncName, CmdIStr,oRet))
            return oRet

        @pyjsonrpc.rpcmethod
        def WyfCmd(self,sParam): # for test
            PrintTimeMsg("WyfCmd.sParam=(%s)!" % (sParam))
            return '{%s}' % sParam
    return RequestHandlerCmdClass

def CallRemoteCmd(sCallType, sHostPort, sServ, sFuncName, lsParam):
    """
        调用远程命令，支持如下两种协议形式
        :param sCallType: JsonRPC/ZmqLRPC/ZmqSRPC
        :param sServ: 服务标识，仅仅是点前面部分，不包括后面的数字
        :param sHostPort: 服务端IP:PORT串
        :param sFuncName: 要调用的函数名
        :param lsParam: 要调用函数参数列表
        :return: 调用返回结果列表
    """
    sUserPass = ':'
    r = None
    if sCallType[:1]=='Z':# JsonRPC/ZmqLRPC/ZmqSRPC
        #若有其它形式协议扩展，在这里增加
        from WyfZmqCmdFuncs import GetZmqRpcClient
        bLongConn = sCallType[3:4]=='L'
        r = GetZmqRpcClient(sHostPort,sUserPass,bLongConn)
    else:
        # from WyfPublicFuncs import GetJsonRpcClient
        r = GetJsonRpcClient(sHostPort,sUserPass)
    try:
        oRet = r.CallCmd(sServ, sFuncName, lsParam)
        r = None
        return oRet
    except Exception, e:
        import traceback
        traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
        return ['E00','r.CallCmd.Exception.e=(%s)' % (str(e))]

class ClassCallRemoteCmd:
    """
        对 CallRemoteCmd 进行了类封装
    """
    def __init__(self, sCallType, sHostPort, sServ, bVerbose=True,sLogFName=''):
        self.sCallType = sCallType
        self.sHostPort = sHostPort
        self.sServ = sServ
        self.bVerbose = bVerbose
        self.sLogFName = sLogFName

    def call(self, sFuncName, lsParam):
        def logMsg(sMsg):
            if not self.bVerbose: return
            if self.sLogFName:
                sFNameOut = self.sLogFName
                with open(sFNameOut,"a") as f: #追加模式输出
                    sS = "[%s]%s\n" % (GetCurrentTimeMS(),sMsg)
                    f.write(sS)
            else:
                PrintMsTimeMsg(sMsg)
        logMsg("call.%s(%s)Beg..." % (sFuncName,str(lsParam)) )
        r = CallRemoteCmd(self.sCallType, self.sHostPort, self.sServ, sFuncName, lsParam)
        logMsg("call.%s(%s)End!!!" % (sFuncName,str(lsParam)) )
        return r

class GetCallStandardCmdClass:
    """
        对 HandleCmdHandleStandard 进行了类封装
    """
    def __init__(self, sServSeq, sPythonDir):
        lsSS = sServSeq.split('.')
        if len(lsSS)<2:
            PrintTimeMsg("ZmqCmdReply.sServSeq=(%s)Error,EXIT!" % (sServSeq))
            sys.exit(-1)
        self.sServ = lsSS[0]
        self.sServSeq = sServSeq
        self.sPythonDir = sPythonDir

    def call(self,sFuncName,lsParam):
        lsServ = [self.sServ]
        lsP = ['%s.%s' % (self.sServ,sFuncName)]
        lsP.extend(lsParam)
        r = HandleCmdHandleStandard(self,lsServ,lsP,[self.sServSeq],self.sPythonDir)
        return r
#--------------------------------------
def GetRedisClient(sRedisParam):
    import redis
    # sRedisParam = '192.168.2.209:6379:6'
    # sRedisParam = '192.168.2.209:6379:6:password'
    sPassword = None # WeiYF.20160414 Redis参数支持密码
    lsP = sRedisParam.split(':')
    if len(lsP)<3:
        PrintTimeMsg("GetRedisClient.sRedisParam=(%s)=Error,EXIT!" % (sRedisParam))
        sys.exit(-1)
    if len(lsP)>=4: sPassword = lsP[3]
    oRedis = redis.StrictRedis(host=lsP[0], port=int(lsP[1]), db=int(lsP[2]), password=sPassword,
                               socket_timeout=30) #WeiYF.20160606 新增超时参数
    PrintTimeMsg("GetRedisClient(%s)ReturnOK..." % (sRedisParam))
    return oRedis

#--------------------------------------
def GetGRpcClient(sJsonRpcHostPort,server_id):
    from grpc import get_proxy_by_addr
    lsHP = sJsonRpcHostPort.split(':')
    if len(lsHP)<2:
        PrintTimeMsg("sJsonRpcHostPort=(%s) error!" % sJsonRpcHostPort)
        return
    endpoint = (lsHP[0], int(lsHP[1]))
    return get_proxy_by_addr(endpoint, server_id)

#--------------------------------------
def importModuleClass(sModule, sClass):
    """
        引入模块类，返回类
    """
    # import sys
    # sys.path.insert(0, '../')
    # WeiYF.20150414 经测试，无需引入上级路径，应该是调用单元已经引入的缘故
    # print "sModule=",sModule
    # print "sClass=",sClass
    m = __import__(sModule, globals(), locals(), [sClass])
    return getattr(m, sClass)

def importClassString(cl):
    """
        通过串，引入模块类，返回类
    """
    d = cl.rfind(".")
    sClass = cl[d+1:len(cl)]
    sModule = cl[0:d]
    return importModuleClass(sModule,sClass)

def StartGRpcServer(sJsonRpcHostPort, sModule, cnMaster, cnWorker):
    from gevent.event import Event
    from grpc import RpcServer

    lsHP = sJsonRpcHostPort.split(':')
    if len(lsHP)<2:
        PrintTimeMsg("sJsonRpcHostPort=(%s) error!" % sJsonRpcHostPort)
        return

    endpoint = (lsHP[0], int(lsHP[1]))
    try:#WeiYF.20150414 经测试，采用importModuleClass才行
        #classMaster = eval("CMaster") #eval(cnMaster)
        #classWorker = eval(cnWorker)
        # classMaster = importClassString("grcs.grsVtrbtctx.CMaster")
        # classWorker = importClassString("grcs.grsVtrbtctx.CWorker")
        classMaster = importModuleClass(sModule,cnMaster)
        classWorker = importModuleClass(sModule,cnWorker)
        master = classMaster(endpoint)
        svr = RpcServer()
        svr.bind(endpoint)
        t1 = classWorker()
        svr.register(t1)
        svr.register(master)
        t1.set_master(svr.get_export_proxy(master))
        svr.start()
        PrintTimeMsg('Starting GRPC server(%s,%s)...' % (sModule,sJsonRpcHostPort))
        wait = Event()
        wait.wait()
    #except KeyboardInterrupt:
    except Exception, e:
        import traceback
        traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
        PrintTimeMsg('StartGRpcServer.Exception.e=(%s)' % (str(e)))
    finally:
        #svr.stop()
        pass
    PrintTimeMsg('Stopping GRPC server(%s,%s)!!!' % (sModule,sJsonRpcHostPort))

#-------------------------------------------------------
def LoadClassFromFile(sPythonFName,sExpectedClass, *args):
    # 从指定Python文件中，动态加载指定类
    import os
    import imp
    try:
        instClass = None
        mod_name,file_ext = os.path.splitext(os.path.split(sPythonFName)[-1])
        if file_ext.lower() == '.py':
            py_mod = imp.load_source(mod_name, sPythonFName)
        elif file_ext.lower() == '.pyc':
            py_mod = imp.load_compiled(mod_name, sPythonFName)
        if hasattr(py_mod, sExpectedClass):
            # instClass = getattr(py_mod, sExpectedClass)(args) #WeiYF.20151022 没有*，会多包括括号，多一层tuple
            instClass = getattr(py_mod, sExpectedClass)(*args) #WeiYF.20151022 应该加上*
    except Exception,e:
        PrintTimeMsg('LoadClassFromFile(%s)=(%s)' % (sPythonFName,str(e)))
        raise  #Using raise with no arguments re-raises the last exception
    return instClass

#-------------------------------------------------------
def HandleCmdHandleStandard(oObj,lsServ,paramJson,paramExtra=None, sPythonDir= ''):
    # WeiYF.20150818 转换调用 CmdHandleStandard 处理
    if (not hasattr(oObj, 'dictServClass')) or (not oObj.dictServClass):
        oObj.dictServClass = {}
        for sServ in lsServ:
            oObj.dictServClass[sServ] = LoadClassFromFile(
                    sPythonDir+'CmdHandle'+sServ+'.py',
                    'CmdHandleStandard',paramExtra)
            # PrintTimeMsg('%s=%s' % (sServ,oObj.dictServClass[sServ]) )
    oJson = paramJson
    typeJson = type(oJson)
    if typeJson==str:
        oJson = eval(oJson)
        typeJson = type(oJson)
    if typeJson==dict:
        sCmdIStr0 = oJson['cmd'] #.get('cmd','') # raise exception
    elif typeJson==list:
        sCmdIStr0 = oJson[0]
    else:
        CmdOStr = ["MMM", "paramJson=(%s).NotSupport!" % (paramJson)]
        return CmdOStr
    (sServ,sCmd) = GetCodeFmString(sCmdIStr0,'.')
    if sServ in set(lsServ):
        oServ = oObj.dictServClass[sServ]
        # PrintTimeMsg('%s=%s' % (sServ,oObj.dictServClass[sServ]) )
        if oServ:
            return oServ.CallByName(sCmd,oJson)
        else:
            CmdOStr = ["MMM", "Cmd=(%s).oServ=None!" % (sCmdIStr0)]
            return CmdOStr
    else:
        CmdOStr = ["MMM", "Cmd=(%s).NotSupport!" % (sCmdIStr0)]
        return CmdOStr

if __name__=="__main__":
    print GetCodeFmString('Code Value1 2 3')
    LoopRunJsonRpcServer('127.0.0.1:8888','',GenJsonRpcReqHandlerClass(None))
