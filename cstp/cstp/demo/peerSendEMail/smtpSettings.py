#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/7/14  WeiYanfeng
    配置发送 EMail 的 SMTP 参数
"""

gDictSMTPByEMail = {
    #以 EMail 为键值，配置相关 SMTP 的参数
    'useracct@163.com': {
        'smtp': 'smtp.163.com',
        'pass': 'change2yourself',
    },
    '23242526@qq.com': {
        'smtp': 'smtp.qq.com',
        'pass': 'change2yourself',
    },
    'useracct@139.com': {
        'smtp': 'smtp.139.com',
        'pass': 'change2yourself',
    },
}

#--------------------------------------
if __name__=='__main__':
    import random
    print random.choice(gDictSMTPByEMail.keys())
