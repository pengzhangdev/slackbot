#! /usr/bin/env python
#
# ttsdriver.py ---
#
# Filename: ttsdriver.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Tue Sep 19 20:46:05 2017 (+0800)
#

# Change Log:
#
#
import os
import sys
import hashlib
import commands

from six.moves import _thread, range, queue
import six

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

class Singleton(object):
        _instance = None
        def __new__(cls, *args, **kw):
            if not cls._instance:
                cls._instance = super(Singleton, cls).__new__(cls, *args, **kw)
            return cls._instance

class TTS(Singleton):
    def __init__(self, config, method):
        self.__ttsdriver = None
        self.__pool = WorkerPool(self.__mplayer)
        self.__pool.start()
        if config == None:
            config = {}

        if method == 'baidu':
            import baidutts
            self.__ttsdriver = baidutts.BaiduTTS(config.get('apikey', ""),
                                                 config.get('secretkey', ""),
                                                 config.get('speed', 5),
                                                 config.get('pitch', 9),
                                                 config.get('volume', 9),
                                                 config.get('person', 3))
        if method == 'iflytek':
            import iflytek
            self.__ttsdriver = iflytek.iflytekTTS(config.get('appid', '59b4d5d4'),
                                                  config.get('voice_name', 'xiaowanzi'),
                                                  config.get('speed', 50),
                                                  config.get('volume', 50),
                                                  config.get('pitch', 50))


    def __text2tts(self, message):
        filename = self.__md5sum(message)
        return self.__ttsdriver.get_tts_audio(message, filename, 'zh')

    def __md5sum(self, contents):
        hash = hashlib.md5()
        hash.update(contents)
        return hash.hexdigest()

    def __mplayer(self, msg):
        f = msg[0]
        st, output = commands.getstatusoutput('mplayer -really-quiet -noconsolecontrols -volume 90 -speed 0.9 {}'.format(f))
        if st != 0:
            print('mplayer output:\n {}'.format(output))

    def __add_to_mplayer(self, f):
        self.__pool.add_task((f, ''))

    def text2play(self, message):
        t, f = self.__text2tts(message)
        self.__add_to_mplayer(f)
