#!/usr/local/bin/python
#-*- coding:utf-8 -*-

"""
Created on 2016-7-6
@author: Weber Juche

统一定义了错误代码和错误消息模版类 CCSTPError
"""

import sys
from weberFuncs import PrintTimeMsg
#--------------------------------------
class CSTPError:
    '''
        集中定义了 CSTP 框架中的错误代码；定义在类中，简化import
    '''
    EE = 'EE'
    ES = 'ES'
    CHECK_AUTH_DEFAULT = 10000
    CHECK_AUTH_P2PKIND = 10001
    CHECK_AUTH_HUBID = 10002
    CHECK_AUTH_NO_CIP = 10003
    CHECK_AUTH_P2P_PAIRID_1 = 10011
    CHECK_AUTH_P2P_PAIRID_2 = 10012
    CHECK_AUTH_P2P_SUFFIX_PWD = 10013
    CHECK_AUTH_P2P_ACCTID_FMT = 10014
    CHECK_AUTH_P2P_ALREADY_ON = 10015
    P2P_SEND_MSG_NO_SUPPORT_0 = 10100
    P2P_SEND_MSG_CIP_NO_PAIRID = 10101
    P2P_SEND_MSG_CIP_NOT_FOUND = 10102
    P2P_SEND_MSG_SUFFIX_FM_ERR = 10103

    dictErrMsgFmt = {
        CHECK_AUTH_DEFAULT : (ES,'CheckAuth.DefaultError!',),
        CHECK_AUTH_P2PKIND : (ES,'sP2PKind={sP2PKind},sAcctId or sAcctPwd error!',),
        CHECK_AUTH_HUBID : (ES,'sP2PKind={sP2PKind},sHubId={sHubId} not match!',),
        CHECK_AUTH_NO_CIP : (ES,'dictObjLinkByCIP.get({sClientIPPort})=None!',),
        CHECK_AUTH_P2P_PAIRID_1 : (ES,'sPairId=({sPairId}) not in lsPairIdAllow!',),
        CHECK_AUTH_P2P_PAIRID_2 : (ES,'sPairId=({sPairId}) NOT found!',),
        CHECK_AUTH_P2P_SUFFIX_PWD : (ES,'sSuffix=({sSuffix}).password NOT match!',),
        CHECK_AUTH_P2P_ACCTID_FMT : (ES,'sAcctId=({sAcctId})Format Error!',),
        CHECK_AUTH_P2P_ALREADY_ON : (ES,'sPairId={sPairId},sSuffix={sSuffix} Already Login on ({sOldIPPort})!',),
        P2P_SEND_MSG_NO_SUPPORT_0 : (ES,'sListSuffixTo=({sListSuffixTo}) include(@) Not supported!',),
        P2P_SEND_MSG_CIP_NO_PAIRID : (ES,'sClientIPPort=({sClientIPPort}) -> sPairId=NULL!',),
        P2P_SEND_MSG_CIP_NOT_FOUND : (ES,'sPairId=({sPairId}),sPeerIdTo={sPeerIdTo} -> sClientIPPortTo=NULL!',),
        P2P_SEND_MSG_SUFFIX_FM_ERR : (ES,'sSuffixFm=({sSuffixFm}), not matches ({sSuffixFmHub})',),
    }

    @classmethod
    def GenErrorMsgHelpList(cls, sCRLF, sHead, sTail):
        sRet = sHead
        for k,v in cls.dictErrMsgFmt.items(): #自动按key排序
            sRet += '%s: %s' % (k,','.join(v)) + sCRLF
        sRet += sTail
        return sRet #str(cls)+'|'+sCRLF

#--------------------------------------
def GenErrorTuple(*args, **kwargs):
    # 生成错误元组，参考 CHubCallbackBasicBase.py 出错出口说明
    # 第一个普通参数是 iErrorNo(sErrorNo) ，第二个可选普通参数是 sErrorDebugMsg
    # 紧接着是零个、一个或多个命名参数，用于格式化生成 sErrorHintMsg
    iErrorNo = 0
    sErrorDebugMsg = ''
    if len(args)>=1: iErrorNo = args[0]
    if iErrorNo==0:
        sErrorHintMsg = 'iErrorNo=%s=, FirstParamError' % iErrorNo
        PrintTimeMsg('GenErrorTuple.%s!' % sErrorHintMsg)
        return ('EX',str(iErrorNo),sErrorHintMsg,'Please Check GenErrorTuple() param!')
    if len(args)>=2: sErrorDebugMsg = args[1]
    tupleFmt = CSTPError.dictErrMsgFmt.get(iErrorNo,())
    if len(tupleFmt)<2:
        sErrorHintMsg = 'dictErrMsgFmt(%s)={%s}=ConfigError' % (iErrorNo,tupleFmt)
        PrintTimeMsg('GenErrorTuple.%s!' % sErrorHintMsg)
        return ('EX',str(iErrorNo),sErrorHintMsg,'Please Check CSTPError.dictErrMsgFmt(%s)!' % iErrorNo)
    sErrorHintMsg = tupleFmt[1].format(**kwargs)
    return (tupleFmt[0],str(iErrorNo),sErrorHintMsg,sErrorDebugMsg)

def GenOkMsgTuple(sOkMsg):
    return ('OK','0',sOkMsg,'')
#--------------------------------------
def testMain():
    # print GenErrorTuple(CSTPError.CHECK_AUTH_P2PKIND,'sHint', sP2PKind='sP2PKind')
    print CSTPError.GenErrorMsgHelpList('\n','','')
    pass

#--------------------------------------
if __name__=='__main__':
    testMain()
