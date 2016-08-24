#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/8/11  WeiYanfeng
    简单串加密、解密函数
    目的是为对一些敏感信息进行一下简单防护。
"""

import base64

def SimpleShiftEncode(sKey, sSrc):
    if sKey=='':  sKey=' ' #若是空串，改为空格
    lsEnc = []
    for i in range(len(sSrc)):
        cKey = sKey[i % len(sKey)]
        cEnc = chr((ord(sSrc[i]) + ord(cKey)) % 256)
        lsEnc.append(cEnc)
    return base64.urlsafe_b64encode("".join(lsEnc))

def SimpleShiftDecode(sKey, sEnc):
    if sKey=='':  sKey=' ' #若是空串，改为空格
    lsDec = []
    sEnc = base64.urlsafe_b64decode(sEnc)
    for i in range(len(sEnc)):
        cKey = sKey[i % len(sKey)]
        cDec = chr((256 + ord(sEnc[i]) - ord(cKey)) % 256)
        lsDec.append(cDec)
    return "".join(lsDec)

def testEncDec():
    sKey = 'key'
    sEnc = SimpleShiftEncode(sKey,'Hello测试test撒大as')
    print sEnc
    sDec = SimpleShiftDecode(sKey,sEnc)
    print sDec

if __name__=="__main__":
    testEncDec()