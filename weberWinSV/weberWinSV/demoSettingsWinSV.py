#!/usr/local/bin/python
# -*- coding:utf-8 -*-
"""    
Created on 2016-7-19
@author: Weber Juche

WeberWinSV 配置参数说明及示例。
适用于 CWinSupervisor 和 CWebSupervisor 两个工具。

"""

gDictConfigByGroupId = {
    # WeberWinSV 配置参数，是新版程序管理设计的核心。

    # workDir 和 logDir 要附带最后路径分隔符，Windows路径要写两个反斜杠
    # programId=cmdProgram标识，用于标识该命令行程序。参与生成日志文件、pid文件等。

    '<groupId>':{ # 以 groupId 为键值，内容是程序组的配置参数字典。
        # 管理程序也以程序组(groupId=程序组标识)为单位进行管理，也支持同时多个。
        # 在 groupId 编码中不能有英文逗号和点号，可以通过下划线加上
        #   dev=开发 和 run=运行 支持两种环境。
        # 为了对参数进行说明，尖括号开始的键值是示例，复制修改时应予以保留。
        'groupTitle': '程序组说明',
        'workDir': '该程序组缺省工作目录',
        'logDir': '该程序组缺省日志目录',
        'err2out': 'True,合并标准错误日志到标准输出，该程序组的缺省设置',
        '<programId>': { # 以 programId 为键值，内容是 cmdProgram 的配置参数字典
            'cmdExec': 'cmdProgram的命令串，请首先在命令行进行测试',
            'cmdTitle':'当前cmdProgram标题，文字描述',
            'shellPopen': 'True/False,调用Popen参数shell参数，缺省是False',
            'workDir': '当前cmdProgram的工作目录',
            'logDir': '当前cmdProgram的日志输出目录',
            'err2out': 'True/False,合并标准错误日志到标准输出',
        },
    },
    'groupExample':{ # 例子程序组, 用于修改替换为实际的配置。
        'logDir': u'./test/log/',
        'workDir': u'./test/',
        #'workDir': u'D:\\WeiYFGitSrc\\PythonProject\\WeberEgg\\GitHub_PythonEggs\\weberWinSV\\weberWinSV\\test\\',
        'err2out': True,
        'programJC': { # 测试程序
            'cmdExec': 'ping juchecar.com',
            'cmdTitle':'测试ping JC',
        },
        'programQQ': { # 测试程序
            'cmdExec': 'ping qq.com',
            'cmdTitle':'测试ping QQ',
        },
        'programQQt': { # 测试程序
            'cmdExec': 'ping qq.com -t',
            'cmdTitle':'测试ping QQ -t',
        },
        'programDirC': { # 测试程序
            'cmdExec': 'dir C:\\',
            'cmdTitle':'测试dir C:',
            'shellPopen': True,  #不设置为True, 会出异常
        },
    },
}


