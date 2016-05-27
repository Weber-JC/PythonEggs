=========================
weberFuncs 包功能说明
=========================

设计目的
====

创建一个Python共享库，内部包含了常用的简单函数。

打印函数
------------

如 PrintTimeMsg 等

时间函数
--------------------

如 GetCurrentTime 等

算法函数
---------------

如 md5、md5file 等


网络访问函数
---------------

如 RequestsHttpGet、RequestsHttpPost 等

打包上传PyPi方法
=========================

相关命令如下
---------------

    $ python setup.py sdist  #编译包
    $ python setup.py sdist upload #上传包
