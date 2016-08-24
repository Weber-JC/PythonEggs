#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/7/7  WeiYanfeng
    将发送 SMTP 邮件封装为类
"""

import sys
import smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

from WyfPublicFuncs import PrintTimeMsg,CatchExcepExitTuple,CatchExcepExitParam

class CSendSMTPMail:
    def __init__(self,sSMTPHost, sAccoutFull, sPassword):
        self.sSMTPHost = sSMTPHost
        self.sAccoutFull = sAccoutFull
        self.sPassword = sPassword
        (self.sAccout, cSep, self.sMailHost) = self.sAccoutFull.partition('@')
        if cSep=='':
            PrintTimeMsg("CSendSMTPMail.sAccoutFull=%s,Error To EXIT!" % (self.sAccoutFull))
            sys.exit(-1)
        PrintTimeMsg("CSendSMTPMail.sSMTPHost=%s,sAccoutFull=%s!" % (
            self.sSMTPHost,self.sAccoutFull))

    def __del__(self):
        pass

    def __sendMail(self, sToEMail, sSubject, sContent, sFromTitle):
        """
            发送邮件
            :param sToEMail: 目标email，多个email可以采用英文分号分开
            :param sSubject: 邮件主题，utf-8编码
            :param sContent: 邮件内容，utf-8编码
            :param sFromTitle: 发件人名称，utf-8编码
            :return: 无
        """
        # print 'sFromTitle', sFromTitle
        msg = MIMEMultipart()
        msg['From'] = sFromTitle.decode('utf-8').encode("gbk","ignore") + "<%s>" % (self.sAccoutFull) #
        sSubject = sSubject.decode('utf-8').encode("gbk","ignore")
        sContent = sContent.decode('utf-8').encode("gbk","ignore")
        msg['Subject'] = sSubject #.encode("gbk","ignore")
        txt = MIMEText(sContent,'html','gbk')
        msg.attach(txt)

        # send email
        if self.sMailHost.upper() in ['QQ.COM']: #QQ邮箱要采用SSL登录
            smtp = smtplib.SMTP_SSL('smtp.qq.com', timeout=30)#连接smtp邮件服务器,端口默认是25
        else:
            smtp = smtplib.SMTP(self.sSMTPHost)
        # smtp.set_debuglevel(1) #会打印邮件发送日志
        smtp.login(self.sAccout,self.sPassword)
        for sTo in sToEMail.split(';'):
            if sTo:
              smtp.sendmail(self.sAccoutFull, sTo, msg.as_string())
        smtp.quit()
        PrintTimeMsg('SendMail.sToEMail(%s) successfully!' % sToEMail)

    def SendMail(self, bThread, sToEMail, sSubject, sContent, sFromTitle='缺省身份'):
        # CatchExcepExitTuple(bThread,'SendMail',self.__sendMail, (sToEMail, sSubject, sContent, sFromTitle))
        CatchExcepExitParam(bThread,'SendMail',self.__sendMail, sToEMail, sSubject, sContent, sFromTitle=sFromTitle)
        return

def testCSendSMTPMail():
    # c = CSendSMTPMail('smtp.163.com', 'xxx@163.com', 'xxx')
    #c.SendMail('weiyf1225@139.com', 'Python Email测试邮件，不是垃圾邮件','This is contents这是内容，用于短信通知')
    #c = CSendSMTPMail('smtp.qq.com', '2328083881@qq.com', '***')
    c = CSendSMTPMail('smtp.139.com', 'weiyf1225@139.com', 'xxx')
    c.SendMail('weiyf1225@qq.com', 'Python Email测试邮件，不是垃圾邮件','This is contents这是内容，用于微信通知','测试身份')


#-----------------------------------------
if __name__ == "__main__":
    testCSendSMTPMail()
    # testQQMail()
