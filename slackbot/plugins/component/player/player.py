#! /usr/bin/env python
#
# mplayer.py ---
#
# Filename: mplayer.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Fri Oct  6 17:57:45 2017 (+0800)
#

# Change Log:
#
#

import os
import sys
import commands
import threading
import logging

from six.moves import _thread, range, queue
import six

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

Lock = threading.Lock()

class WorkerPool(object):
    def __init__(self, func, nworker=1):
        self.nworker = nworker
        self.func = func
        self.queue = queue.Queue()

    def start(self):
        for __ in range(self.nworker):
            _thread.start_new_thread(self.do_work, tuple())

    def add_task(self, msg):
        self.queue.put(msg)

    def do_work(self):
        while True:
            msg = self.queue.get()
            self.func(msg)

class Player(object):
    _instance = None
    _inited = False
    def __init__(self):
        if Player._inited:
            return

        print("Init singleton Player")
        Player._inited = True

        self.__player = None
        self.__pool = WorkerPool(self.__play)
        self.__pool.start()

    def __new__(cls, *args, **kw):
        if not cls._instance:
            try:
                Lock.acquire()
                if not cls._instance:
                    cls._instance = super(Player, cls).__new__(cls, *args, **kw)
            finally:
                Lock.release()
        return cls._instance

    def __play(self, msg):
        f = msg[0]
        if self.__player != None:
            self.__player.play(f)

    def play(self, filename):
        if self.__player == None:
            _LOGGER.error("lower player not inited")
            return "Failed to play the audio"
        self.__pool.add_task((filename, ''))

    def update_config(self, driver='mplayer'):
        if self.__player != None:
            return
        if driver == 'mplayer':
            import mplayer
            self.__player = mplayer.MPlayer()

if __name__ == '__main__':
    player = Player()
    player.update_config(driver='mplayer')
    player.play('/tmp/1.mp3')
    import time
    time.sleep(10000)
