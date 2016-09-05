#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
    2015/11/5  WeiYanfeng
    判断链接状态，并自动重连的Redis链接封装类
"""

import sys
import time

from WyfPublicFuncs import PrintTimeMsg,GetCurrentTime
from JsonRpcFuncs import GetRedisClient

class CAutoConnectRedis:
    def __init__(self, sClientName):
        self.sClientName = sClientName
        self.dictRedisByParam = {}

    def GetRedis(self, sRedisParam):
        dictRedis = self.dictRedisByParam.get(sRedisParam,{})
        oRedis = dictRedis.get('oRedis',None)
        bNeedNew = not oRedis
        try:
            if oRedis:
                oRedis.incr('KV_COUNT_COMMAND_%s' % self.sClientName)
                dictRedis['tmLastCommand'] = time.time()
        except Exception, e: #ConnectionError TimeoutError
            import traceback
            traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
            PrintTimeMsg('GetRedis.COMMAND.Exception.e=(%s)' % (str(e)))
            bNeedNew = True
        if bNeedNew:
            try:
                oRedis = GetRedisClient(sRedisParam)
                oRedis.incr('KV_COUNT_CONNECT_%s' % self.sClientName)
                dictRedis['oRedis'] = oRedis
                dictRedis['tmLastConnect'] = time.time()
                self.dictRedisByParam[sRedisParam] = dictRedis
            except Exception, e: #ConnectionError TimeoutError
                import traceback
                traceback.print_exc() #WeiYF.20151022 打印异常整个堆栈 这个对于动态加载非常有用
                PrintTimeMsg('GetRedis.CONNECT.Exception.e=(%s)' % (str(e)))
                return None
        return oRedis

def testCAutoConnectRedis():
    acb = CAutoConnectRedis('Windows')
    oRedis = acb.GetRedis('192.168.2.209:6379:6')
    print oRedis.hgetall('HASH_Proxy1_8888_STATUS')
    oRedis = acb.GetRedis('192.168.2.209:6379:6')
    print oRedis.hgetall('HASH_Proxy1_8888_STATUS')
    print oRedis.hgetall('HASH_Proxy1_8899_STATUS')
    print acb.dictRedisByParam

#-------------------------------
if __name__ == '__main__':
    testCAutoConnectRedis()