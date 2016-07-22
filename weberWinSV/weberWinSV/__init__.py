#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
2016/7/21  WeiYanfeng

weberWinSV 包实现了Windows 平台下的程序管理工具，类似于Linux系统下的 Supervisor 。
该包实际内含两个管理工具：
1. CWinSupervisor 是启动管理其它“命令行程序”的管理工具。可以单独部署。
2. CWebSupervisor 是监控 CWinSupervisor 运行状态的工具。可以根据需要部署。

"""
from CWinSupervisor import StartCWinSupervisor

if __name__ == '__main__':
    pass