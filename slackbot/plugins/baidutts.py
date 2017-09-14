#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# baidutts.py ---
#
# Filename: baidutts.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Sep 10 13:12:50 2017 (+0800)
#

# Change Log:
#
#

import requests
import logging
import json
import logging
import os

try:
    from pydub import AudioSegment
except Exception as e:
    print  'Missing module pydub, please install it'

_Log=logging.getLogger(__name__)

TOKEN_INTERFACE = 'https://openapi.baidu.com/oauth/2.0/token'
TEXT2AUDIO_INTERFACE = 'http://tsn.baidu.com/text2audio'


def not_none_return(obj, defobj):
    if obj:
        return obj
    else:
        return defobj

class BaiduTTS():
    def __init__(self, apikey, secretkey, speed, pitch, volume, person):
        self.__apikey = apikey
        self.__secretkey = secretkey
        self.__speed = not_none_return(speed, 4)
        self.__pitch = not_none_return(pitch, 5)
        self.__volume = not_none_return(volume, 9)
        self.__person = not_none_return(person, 1)
        self.__token = self.getToken()
        _Log.info("token =====>" + self.__token)

    def getToken(self):
        resp = requests.get(TOKEN_INTERFACE,params={'grant_type': 'client_credentials','client_id':self.__apikey,'client_secret':self.__secretkey})
        if resp.status_code != 200:
            _Log.error('Get ToKen Http Error status_code:%s' % resp.status_code)
            return None
        resp.encoding = 'utf-8'
        tokenJson =  resp.json()
        if not 'access_token' in tokenJson:
            _Log.error('Get ToKen Json Error!')
            return None
        return tokenJson['access_token']

    def __insert_silent(self, media_file, ftype):
        try:
            silent = AudioSegment.silent(duration=1000)
            sound1 = AudioSegment.from_file(media_file, ftype)
            combined = silent + sound1 + silent
            combined.export(media_file, format=ftype)
        except Exception as e:
            print("insert_silent failed file {} error {}".format(media_file, e))

    def __save_file(self, data, _tmp_file = '/tmp/test.mp3'):
        with open(_tmp_file, 'w') as f:
            f.write(data)

    def get_tts_audio(self, message, filename, language, options=None):
        if self.__token == None:
            self.__token = self.getToken()

        if self.__token == None:
            _Log.error('get_tts_audio Self.ToKen is nil')
            return

        resp = requests.get(TEXT2AUDIO_INTERFACE,params={'tex':message,'lan':language,'tok':self.__token,'ctp':'1','cuid':'HomeAssistant','spd':self.__speed,'pit':self.__pitch,'vol':self.__volume,'per':self.__person})

        if resp.status_code == 500:
            _Log.error('Text2Audio Error:500 Not Support.')
            return
        if resp.status_code == 501:
            _Log.error('Text2Audio Error:501 Params Error')
            return
        if resp.status_code == 502:
            _Log.error('Text2Audio Error:502 TokenVerificationError.')
            _Log.Info('Now Get Token!')
            self.__token = self.getToken()
            return self.get_tts_audio(message,language,options)
        if resp.status_code == 503:
            _Log.error('Text2Audio Error:503 Composite Error.')
            return
        if resp.status_code != 200:
            _Log.error('get_tts_audio Http Error status_code:%s' % resp.status_code)
            return

        data = resp.content
        fname = os.path.join('/tmp/' + filename + '.' + 'mp3')
        self.__save_file(data, fname)
        self.__insert_silent(fname, 'mp3')
        return ('mp3', fname)

if __name__ == '__main__':
    tts = BaiduTTS('XXXXXXXXXXXXXXXXXXX', 'xxxxxxxxxxxxx', 5, 9, 9, 3)
    def md5sum(contents):
        import hashlib
        hash = hashlib.md5()
        hash.update(contents)
        return hash.hexdigest()

    import sys
    basename = md5sum(sys.argv[1])
    t, f = tts.get_tts_audio(sys.argv[1], basename, 'zh');

    def mplayer(f):
        import commands
        st, output = commands.getstatusoutput('mplayer -really-quiet -noconsolecontrols -volume 82 {}'.format(f))

    mplayer(f)
    import os
    os.remove(f)
