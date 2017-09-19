#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# iflytek.py ---
#
# Filename: iflytek.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Thu Sep 14 09:01:20 2017 (+0800)
#

# Change Log:
#
#


import time
from ctypes import *
from io import BytesIO
import wave
import platform
import logging
import os
import contextlib

logging.basicConfig(level=logging.DEBUG)

BASEPATH=os.path.split(os.path.realpath(__file__))[0]

def not_none_return(obj, defobj):
    if obj:
        return obj
    else:
        return defobj

class iflytekTTS():
    def __init__(self, appid=None, voice_name=None, speed=None, volume=None, pitch=None):
        self.__appid = not_none_return(appid, '59b4d5d4')
        self.__voice_name = not_none_return(voice_name, 'xiaowanzi')
        self.__speed = not_none_return(speed, 50)
        self.__volume = not_none_return(volume, 50)
        self.__pitch = not_none_return(pitch, 50)
        self.__cur = cdll.LoadLibrary(os.path.join(BASEPATH, 'iflytek/libmsc.so'))
        self.__iflytek_init()

    def __save_file(self, raw_data, _tmpFile = '/tmp/test.wav'):
        if os.path.exists(_tmpFile) :
            return

        tmpFile = _tmpFile + '.tmp'
        with contextlib.closing(wave.open(tmpFile , 'w')) as f:
            f.setparams((1, 2, 16000, 262720, 'NONE', 'not compressed'))
            f.writeframesraw(raw_data)

        os.rename(tmpFile, _tmpFile)

    def __iflytek_init(self):
        MSPLogin = self.__cur.MSPLogin

        ret = MSPLogin(None,None,'appid = {}, work_dir = .'.format(self.__appid))
        if ret != 0:
            logging.error("MSPLogin failed, error code: {}".format(ret))
            return False
        return True

    def get_tts_audio(self, src_text, filename, language='zh', options=None):
        fname = os.path.join('/tmp/', filename + '.' + 'wav')

        QTTSSessionBegin = self.__cur.QTTSSessionBegin
        QTTSTextPut = self.__cur.QTTSTextPut

        QTTSAudioGet = self.__cur.QTTSAudioGet
        QTTSAudioGet.restype = c_void_p

        QTTSSessionEnd = self.__cur.QTTSSessionEnd

        ret_c = c_int(0)
        ret = 0

        session_begin_params="voice_name = {}, text_encoding = utf8, sample_rate = 16000, speed = {}, volume = {}, pitch = {}, rdn = 2".format(self.__voice_name, self.__speed, self.__volume, self.__pitch)
        sessionID = QTTSSessionBegin(session_begin_params, byref(ret_c))
        if ret_c.value == 10111: # 没有初始化
            if self.__iflytek_init():
                return self.get_tts_audio(src_text, filename)

        if ret_c.value != 0:
            logging.error("QTTSSessionBegin failed, error code: {}".format(ret_c.value))
            return

        ret = QTTSTextPut(sessionID, src_text, len(src_text), None)
        if ret != 0:
            logging.error("QTTSTextPut failed, error code:{}".format(ret))
            QTTSSessionEnd(sessionID, "TextPutError")
            return

        logging.info("正在合成 [{}]...".format(src_text))

        audio_len = c_uint(0)
        synth_status = c_int(0)

        f = BytesIO()
        while True:
            p = QTTSAudioGet(sessionID, byref(audio_len), byref(synth_status), byref(ret_c))
            if ret_c.value != 0:
                logging.error("QTTSAudioGet failed, error code: {}".format(ret_c))
                QTTSSessionEnd(sessionID, "AudioGetError")
                break

            if p != None:
                buf = (c_char * audio_len.value).from_address(p)
                f.write(buf)

            if synth_status.value == 2:
                self.__save_file(f.getvalue(), fname)
                break

            time.sleep(0.5)

        logging.info('合成完成！')
        ret = QTTSSessionEnd(sessionID, "Normal")
        if ret != 0:
            logging.error("QTTSSessionEnd failed, error code:{}".format(ret))

        return ('wav', fname)


if __name__ == '__main__':
    tts = iflytekTTS()
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
    print f

    basename = md5sum(sys.argv[1][:-1])
    t, f = tts.get_tts_audio(sys.argv[1][:-1], basename, 'zh');
    print f

    #os.remove(f)

