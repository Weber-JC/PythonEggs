#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/8/9  WeiYanfeng
    将发送微信客服消息封装为类
"""

import sys
import time
import json

from WyfPublicFuncs import PrintTimeMsg,HttpGet,HttpPostJson,\
    CatchExcepExitTuple,CatchExcepExitParam

class CSendCustomMsgWX:
    def __init__(self,sAPPID, sAPPSECRET):
        self.sAPPID = sAPPID
        self.sAPPSECRET = sAPPSECRET

        self.sWxUrlPrefix = 'https://api.weixin.qq.com/cgi-bin/' # 微信API的URL前缀

        # PrintTimeMsg("CSendSMTPMail.sAccoutFull=%s,Error To EXIT!" % (self.sAccoutFull))
        self.sAccessToken = ''  # 当前令牌
        self.iTmTokenExpire = 0 # 令牌时效时间戳

    def __del__(self):
        pass

    def __getWxUrl(self, sParam):
        return self.sWxUrlPrefix + sParam

    def __getToken(self):
        sParam = 'grant_type=client_credential&appid=%s&secret=%s' % (self.sAPPID, self.sAPPSECRET)
        sUrl = self.__getWxUrl('token?%s' % sParam)
        sRet = HttpGet(sUrl)
        # print ("Get(%s)=(%s)" % (sUrl,sRet))
        if sRet:
            jsonDict = json.loads(sRet)
            if jsonDict:
                self.sAccessToken = jsonDict.get("access_token","")
                if self.sAccessToken=="":
                    PrintTimeMsg("__getToken=(%s)error" % (str(jsonDict)))
                else:
                    self.iTmTokenExpire = time.time()+int(jsonDict.get("expires_in","0"))
                    PrintTimeMsg("__getToken.expires_time=(%s)" % (time.strftime(
                        "%Y%m%d-%H%M%S",time.localtime(self.iTmTokenExpire)) ))
                # print "self.access_token=",self.access_token
            else:
                PrintTimeMsg("__getToken=(%s)error" % (str(jsonDict)))
        else:
            PrintTimeMsg("__getToken=None")

    def GetTokenWhenNeed(self, bThread): #
        if self.sAccessToken=='' or (time.time()+60>=self.iTmTokenExpire): #提早60s
            # CatchExcepExitTuple(bThread,'getToken',self.__getToken,())
            CatchExcepExitParam(bThread,'getToken',self.__getToken)
            # self.__getToken()
        return self.sAccessToken

    def SendCustomMsg(self, bThread, sOpenId, sMsg):
        self.GetTokenWhenNeed(bThread) #必要时获取Token
        return CatchExcepExitParam(bThread,'sendCustomMsg',self.__SendCustomMsg,sOpenId, sMsg)

    def __SendCustomMsg(self, sOpenId, sMsg):
        # 参见 https://mp.weixin.qq.com/wiki?t=resource/res_main&id=mp1421140547&token=&lang=zh_CN
        # http请求方式: POST
        #   https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=ACCESS_TOKEN
        # 发送客服消息
        # self.sAccessToken = 'bc3_B_Fqtsy0gtSwLsVSikWmKx2epGVo1k10YjycsODhL8Kvlp8s2QwW9GLp9y0PCbc9sKNa5n9XKHIegBu0tphuKphCYhJGaoMWzteihah0KasuO5j0E3A4hBOktfzqOIEiACAXRN'
        sUrl = self.__getWxUrl('message/custom/send?access_token=%s' % self.sAccessToken)
        dictData = {
            "touser": sOpenId,
            "msgtype": "text",
            "text": {
                 "content": sMsg,
            }
        }
        sData = json.dumps(dictData,ensure_ascii=False)
        sRet = HttpPostJson(sUrl,sData) #RequestsHttpPost
        # sRet = RequestsHttpPost(sUrl,dictData) #使用该函数会出错
        jsonRet = json.loads(sRet)
        errcode = jsonRet.get('errcode',0)
        if errcode==0:
            PrintTimeMsg('__SendCustomMsg(%s)=OK!' % sOpenId)
        else:
            errmsg = jsonRet.get('errmsg','@DefaultError')
            PrintTimeMsg('__SendCustomMsg(%s)=Error(%s,%s)!' % (sOpenId,errcode,errmsg))
        return errcode

def testCSendCustomMsgWX():
    sAPPID = "sAPPID"
    sAPPSECRET = "sAPPSECRET"
    c = CSendCustomMsgWX(sAPPID, sAPPSECRET)
    # print c.GetTokenWhenNeed()
    # print c.GetTokenWhenNeed()
    c.SendCustomMsg(False,'oMM04uKzqAAadTk1pbLQSD2sJn_w','测试test一下客服消息123\n真不错！')

#-----------------------------------------
if __name__ == "__main__":
    testCSendCustomMsgWX()
