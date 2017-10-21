#! /usr/bin/env python
#
# MiVacuum.py ---
#
# Filename: MiVacuum.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Oct  7 18:50:54 2017 (+0800)
#

# Change Log:
#
#

import threading
import logging
import time
import datetime
from API.vacuum import Vacuum

Lock = threading.Lock()
_LOGGER = logging.getLogger(__name__)

class MiVacuum(object):
    """MiVacuum API"""
    _instance = None
    _inited = False
    _NAME = 'vacuum.xiaomi_vacuum_cleaner'
    CHARGING='Charging'
    CLEANING='Cleaning'
    ERROR='Error'
    def __init__(self):
        if MiVacuum._inited:
            return

        MiVacuum._inited = True
        _LOGGER.info("Init singleton MiVacuum")
        self._vacuum = Vacuum()
        self._started = False
        self._suspend = False

    def __new__(cls, *args, **kw):
        if not cls._instance:
            try:
                Lock.acquire()
                if not cls._instance:
                    cls._instance = super(MiVacuum, cls).__new__(cls, *args, **kw)
            finally:
                Lock.release()
        return cls._instance

    def update_config(self, config):
        pass

    def start(self):
        if self._vacuum:
            self._vacuum.start(MiVacuum._NAME)
            self._started = True


    def stop(self):
        if self._vacuum:
            self._vacuum.stop(MiVacuum._NAME)
            self._started = False

    def locate(self):
        if self._vacuum:
            self._vacuum.locate(MiVacuum._NAME)

    def state(self):
        if self._vacuum:
            return self._vacuum.get_state(MiVacuum._NAME)

    def suspend(self, state):
        # True or False
        self._suspend = state

    def history(self):
        if self._vacuum:
            return self._vacuum.get_history(MiVacuum._NAME)

    def automation(self):
        now = datetime.datetime.now()
        # week = now.isoweekday()
        # _LOGGER.debug("week = {}".format(week))
        # if week != 1 and week != 3 and week != 5:
        #     return

        if self._suspend:
            return

        state = self.state()
        _LOGGER.info("state = {}".format(state))
        if state == MiVacuum.ERROR:
            return

        _LOGGER.info("_started = {}".format(self._started))
        if self._started == True:
            if state == MiVacuum.CHARGING:
                self._started = False
            return

        for history in self.history():
            if history.get('status', '') == MiVacuum.CLEANING:
                _LOGGER.info("Cleaning in the past 24h")
                return

        self.start()
        time.sleep(30)      # waiting for the STATE of HA updated


if __name__ == '__main__':
    logging.basicConfig()
    _LOGGER.setLevel(logging.DEBUG)
    mi = MiVacuum()
    mi.locate()
    mi.automation()
    mi.stop()
