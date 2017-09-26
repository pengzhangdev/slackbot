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

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kw)
        return cls._instance
