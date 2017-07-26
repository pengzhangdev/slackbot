#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# anywhere.py ---
#
# Filename: anywhere.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Mon Jul 24 13:37:15 2017 (+0800)
#

# Change Log:
#
#

import sys
import os
import urllib
import urllib2
import cookielib
import requests
import json
from six.moves import _thread
import time

SHARED_DIR_ROOT='/extdisk/sda1/'
DOWNLOAD_DIR='/extdisks/sda1/下载/'
#DOWNLOAD_DIR='/home/werther/Music/'

class SendAnywhere (object):
    API_ENDPOINTS = "https://send-anywhere.com"
    RESPONSE_CODE = {
        200:"OK",
        400:"Bad Request. Invalid request query string.",
        403:"Bad Request. Invalid request query string.",
        404:"Not Found. Invalid key",
        429:"Too Many Request. To keep the amount of spam on Send Anywhere as low as possible.",
        500:"Internal Server Error. Something went wrong on our side. We're very sorry."
    }

    def __init__(self, api_key, msg=None):
        self.cookie = cookielib.CookieJar()
        self.handler = urllib2.HTTPCookieProcessor(self.cookie)
        self.opener = urllib2.build_opener(self.handler)
        self.api_key = api_key
        self.download_progress = 1.0
        self.msg = msg
        self.inited = False

    def __update(self):
        request_url = "https://send-anywhere.com/web/v1/device?api_key={}&profile_name=miroute".format(self.api_key)
        response = self.opener.open(request_url)
        self.inited = True

    def __upload_file(self, url, filename, timeout):
        try:
            with open(filename, 'rb') as f:
                response = requests.post(url, files={'file': f}, timeout=timeout)
        except requests.exceptions.Timeout:
            print "Timeout waiting for post"
        print("Send file done response {}".format(response))

    def __upload_file_stream(self, url, filename, timeout):
        import poster
        poster.streaminghttp.register_openers()
        with open(filename, 'rb') as f:
            datagen, headers = poster.encode.multipart_encode({'file': f})
            print("upload url: {}".format(urllib.quote(url.encode('utf-8'))))
            request = urllib2.Request(urllib.quote(url.encode('utf-8')), datagen, headers)
            resp = None
            try:
                resp = urllib2.urlopen(request, timeout=timeout)
            except urllib2.HTTPError as error:
                print(error)
                print(error.fp.read())

        print("Send file done response {}".format(resp))

    def send(self, filename):
        if not self.inited:
            self.__update()

        key_api_url = "{}/web/v1/key".format(SendAnywhere.API_ENDPOINTS)

        response = self.opener.open(key_api_url)
        jdata = json.loads(response.read())
        print("share key: {}".format(jdata['key']))
        #print("{}".format(jdata))
        timeout = jdata['expires_time'] - jdata['created_time']
        _thread.start_new_thread(self.__upload_file_stream,
                                 (jdata['weblink'], filename, timeout))
        #self.__upload_file(jdata['weblink'], filename, timeout)
        #time.sleep(timeout)
        return (timeout, jdata['key'])

    def __download_callback(self, downsize, totalsize):
        self.download_progress = float(downsize) / float(totalsize)

    def __download_file(self, url, fpath, filesize, callback=None):
        count = 0
        blocksize = 1024*64
        r = requests.get(url, stream=True)
        with open(fpath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=blocksize):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    if callback:
                        count += 1
                        callback(count*blocksize, filesize)
        callback(filesize, filesize)
        u = url + '&mode=status&_={}'.format(int(time.time()))
        #print('status url {}'.format(u))
        res = self.opener.open(u)
        jdata = json.loads(res.read())
        dirname = os.path.dirname(fpath)
        fp = jdata.get('name', fpath).encode('utf-8')
        #print('jdata {}'.format(jdata))
        if fp != fpath:
            fp = os.path.join(dirname, fp)
            os.rename(fpath, fp)
        if self.msg:
            self.msg.reply("Finish downloading {} !".format(fp))

    def receive(self, name, key, msg=None):
        if 1 - self.download_progress > 0.01:
            print("Download in progress, please wait!!")
            return self.download_progress
        self.msg = msg
        key_api_url = "{}/web/v1/key/{}".format(SendAnywhere.API_ENDPOINTS, key)
        response = self.opener.open(key_api_url)
        jdata = json.loads(response.read())
        #print("{}".format(jdata))
        _thread.start_new_thread(self.__download_file,
                                 (jdata['weblink'],
                                  name,
                                  jdata['file_size'],
                                  self.__download_callback))
        return 0


if __name__ == '__main__':
    s = SendAnywhere("")
    #timeout, key = s.send('Lonely.mp3')
    # print("shared key : {}".format(key))
    # time.sleep(timeout)
    s.receive('mp3', 156724)
    sys.exit(1)



import zipfile
def unzip(zippath, dest):
    zippath = os.path.join(DOWNLOAD_DIR, zippath)
    fullunzipdirname = os.path.join(DOWNLOAD_DIR, dest)
    zfile = zipfile.ZipFile(zippath, 'r')
    for eachfile in zfile.namelist():
        eachfilename = os.path.normpath(os.path.join(fullunzipdirname, eachfile))
        eachdirname = os.path.dirname(eachfilename)
        if eachfile.endswith("/"):
            # dir
            os.makedirs(eachfilename)
            continue
        if not os.path.exists(eachdirname):
            os.makedirs(eachdirname)
        fd = open(eachfilename, 'wb')
        fd.write(zfile.read(eachfile))
        fd.close()


from slackbot.bot import plugin_init
from slackbot.bot import respond_to

_enable = False
_anywhere = None
@plugin_init
def init_anywhere(config):
    global _enable
    global _anywhere
    api_key = config.get('api', '')
    _enable = config.get('enable', False)
    _anywhere = SendAnywhere(api_key)

@respond_to(r'anywhere (.*)')
def anywhere_command(message, rest):
    global _enable
    global _anywhere
    if not _enable:
        message.reply("SendAnywhere not enabled")
        return

    argv = ['anywhere'] + rest.split()
    print("{}".format(argv))
    command = argv[1]
    if command == 'send':
        # anywhere send [filepath]
        if len(argv) < 3:
            message.reply("Usage: anywhere send  [filepath]")
        if argv[2] == None:
            message.reply("Usage: anywhere send  [filepath]")
        filepath = ' '.join(argv[2:])
        (timeout, key) = _anywhere.send(os.path.join(DOWNLOAD_DIR, filepath))
        message.reply('Shared file key {} expired in {} seconds'.format(key, timeout))
        return

    if command == 'receive':
        # anywhere recv key filename
        if len(argv) < 4:
            message.reply("Usage: anywhere receive [key] [filename]")
        if argv[2] == None or argv[3] == None:
            message.reply("Usage: anywhere receive [key] [filename]")
        key = argv[2]
        filename = ' '.join(argv[3:])
        filename = os.path.join(DOWNLOAD_DIR, key + '_' + filename)
        ret = _anywhere.receive(filename, key, message)
        if ret == 0:
            message.reply("Start downloading {} to {}".format(key, filename))
        else:
            message.reply("Last download not done, progress {}".format(ret))
        return

    if command == 'ls':
        print("command ls")
        if len(argv) == 2:
            argv = argv + ['{}'.format(DOWNLOAD_DIR)]
        for arg in argv[2:] :
            files = os.listdir(arg)
            message.reply('{}'.format('\n'.join(files[:])))
        return

    if command == 'unzip':
        print("command unzip")
        if len(argv) != 3 and len(argv) != 4:
            message.reply("Usage: anywhere unzip [zipfile]")
            return
        zippath = argv[2]
        if len(argv) == 4:
            dest = argv[4]
        else:
            dest = os.path.dirname(zippath)
        try:
            unzip(zippath, dest)
        except Exception as e:
            print("{}".format(e))
            message.reply("Unzip Failed")
            t, v, tb = sys.exc_info()
            raise t, v, tb
            return
        message.reply("Unzip success")
        return

    message.reply("Usage: The ROOT is {}\n"
                  "     anywhere ls\n"
                  "     anywhere send [filepath]\n"
                  "     anywhere receive [key] [filename]\n"
                  "     anywhere unzip [zipfile]".format(DOWNLOAD_DIR))
