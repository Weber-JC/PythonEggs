#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/9/28  WeiYanfeng
    Hub Demo
"""

gDictP2PLayoutByPairId = {
    # P2PLayout sPairId配置参数
    # 以 sPairId 为键值，内容是 sSuffix = sPassword 组成的键值对
    '@sPairId': {
        '@sSuffix': '@sPassword',
    },
    'MonitHub': {
        # WeiYF.20160708 sSuffix 编码规划建议：
        #    采用英文句点(.)分隔。
        #    前缀首字母是英文叹号(!)表示是保留含义代码。
        #    !Service 前缀，表示传统意义上的请求应答服务。
        '!Service.SendMail': 'send0707@mail', #邮件通知服务
        'Monitor.Python': 'mp0707@hub',
        'Test.SendEMail': 'ts0928@1519',
        'GatherApp.DevCoding': 'zAphtYbL',
        'GatherApp.LocalSide': 'dHbI34f1',
        'GatherApp.CloudWork': 'QeUDF7Yz',
        'GatherApp.CloudTest': 'tmQAuBtl',
    },
}

gDictIPPortByParam = {
    # CSTP 运行IPPort参数，以 sHostName4Param 为键值
    'RunOnHost': {  #运行环境
        'sIPPort': '0.0.0.0:9110',
    },
}
