#! /usr/bin/env python
#
# singleton.py ---
#
# Filename: singleton.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Tue Sep 26 20:33:55 2017 (+0800)
#

# Change Log:
#
#

import threading

Lock = threading.Lock()

class Singleton(object):
    _instance = None
    _inited = False
    def __init__(self):
        if Singleton._inited:
            return
        Singleton._inited = True
        print("init")
    def __new__(cls, *args, **kw):
        if not cls._instance:
            try:
                Lock.acquire()
                if not cls._instance:
                    cls._instance = super(Singleton, cls).__new__(cls, *args, **kw)
            finally:
                Lock.release()
        return cls._instance


if __name__ == '__main__':
    instance1 = Singleton()
    instance2 = Singleton()

    print id(instance1)
    print id(instance2)
