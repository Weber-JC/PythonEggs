#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
    2016-7-6  WeiYanfeng
    启动 TCmdStringHub 服务

pip install weberFuncs
pip install cstp
pip install --upgrade --force-reinstall cstp
"""
import sys
from weberFuncs import PrintTimeMsg,md5
from cstp import StartCmdStringHub,CHubCallbackP2PLayout
from cstpHubSettings import gDictP2PLayoutByPairId,gDictIPPortByParam

def runCmdStringHub(sHostName4Param):
    global gDictP2PLayoutByPairId,gDictIPPortByParam
    dictParam = gDictIPPortByParam.get(sHostName4Param,{})
    if not dictParam:
        PrintTimeMsg('runCmdStringHub.get(%s)={}' % sHostName4Param)
        sys.exit(-1)
    sServerIPPort = dictParam.get('sIPPort', '0.0.0.0:9110')
    sHubId = md5('%s:%s:@HubId' % (sHostName4Param,sServerIPPort))
    tupleClsParamP2PLayout = (sHubId,gDictP2PLayoutByPairId,)
    StartCmdStringHub(sHostName4Param,sServerIPPort,
                      CHubCallbackP2PLayout, tupleClsParamP2PLayout,
                      __file__)

#--------------------------------------
if __name__ == '__main__':
    # sHostName4Param = 'LocalTest'
    sHostName4Param = 'RunOnHost'
    if len(sys.argv)>=2:
        sHostName4Param = sys.argv[1]
    runCmdStringHub(sHostName4Param)
