#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# tts.py ---
#
# Filename: tts.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Sep 10 16:24:08 2017 (+0800)
#

# Change Log:
#
#
import os
import sys
import baidutts
import hashlib
import commands

from slackbot.bot import plugin_init
from slackbot.bot import respond_to

try:
    from pydub import AudioSegment
except Exception as e:
    print  'Missing module pydub, please install it'

class TTS(object):
    def __init__(self, config, method):
        self.__ttsdriver = None
        if method == 'baidu':
            self.__ttsdriver = baidutts.BaiduTTS(config.get('apikey', ""),
                                                 config.get('secretkey', ""),
                                                 config.get('speed', 5),
                                                 config.get('pitch', 9),
                                                 config.get('volume', 9),
                                                 config.get('person', 3))


    def __insert_silent(self, media_file, ftype):
        try:
            silent = AudioSegment.silent(duration=1000)
            sound1 = AudioSegment.from_file(media_file, ftype)
            combined = silent + sound1
            combined.export(media_file, format=ftype)
        except Exception as e:
            print("{}".format(e))

    def __text2tts(self, message):
        return self.__ttsdriver.get_tts_audio(message, 'zh')

    def __md5sum(self, contents):
        hash = hashlib.md5()
        hash.update(contents)
        return hash.hexdigest()

    def __mplayer(self, f):
        st, output = commands.getstatusoutput('mplayer -really-quiet -noconsolecontrols -volume 85 -speed 0.8 {}'.format(f))
        if st != 0:
            print('mplayer output:\n {}'.format(output))

    def text2play(self, message):
        t, d = self.__text2tts(message)
        basename = self.__md5sum(d)
        basename = os.path.join('/tmp/' + basename + '.' + t)
        with open(basename, 'w') as f:
            f.write(d)
        self.__mplayer(basename)
        os.remove(basename)

tts_obj = None

@plugin_init
def init_tts(config):
    global tts_obj
    enable = config.get('enable', False)
    driver = config.get('driver', 'baidu')
    if enable:
        tts_obj = TTS(config, driver)

@respond_to(r'tts (.*)')
def tts_command(message, rest):
    global tts_obj

    tts_obj.text2play(rest)
