#! /usr/bin/env python
#
# Member.py ---
#
# Filename: Member.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Oct  8 15:34:00 2017 (+0800)
#

# Change Log:
#
#

import threading
import logging


from API.DeviceTracker import DeviceTracker

Lock = threading.Lock()
_LOGGER = logging.getLogger(__name__)

class Member(object):
    """Home Member"""
    _instance = None
    _inited = False
    HOME = DeviceTracker.HOME
    AWAY = DeviceTracker.AWAY

    def __init__(self):
        if Member._inited:
            return

        Member._inited = True
        _LOGGER.info("Inite singleton Member")
        self._deviceTracker = DeviceTracker()

    def __new__(cls, *args, **kw):
        if not cls._instance:
            try:
                Lock.acquire()
                if not cls._instance:
                    cls._instance = super(Member, cls).__new__(cls, *args, **kw)
            finally:
                Lock.release()
        return cls._instance

    def state(self):
        pass

    def update_config(self, config):
        pass

    def automation(self):
        pass
