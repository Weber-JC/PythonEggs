#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""
    2016/7/14  WeiYanfeng
    借助 json 实现了字典对象的序列化到文件并加载
"""

import json
class CSerialJson:
    def __init__(self, sFNameSerial):
        self.sFNameSerial = sFNameSerial

    def Save(self, dictJson):
        with open(self.sFNameSerial,"w") as f:
            f.write(json.dumps(dictJson))

    def Load(self):
        with open(self.sFNameSerial,"r") as f:
            return json.loads(f.read())

def testSerial():
    c = CSerialJson('test.txt')
    print 'LOAD=', c.Load()
    c.Save({'foo': 'bar', 'test': '汉字'})
    print 'END'
    sys.exit(0)
#--------------------------------------
if __name__=='__main__':
    testSerial()