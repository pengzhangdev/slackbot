#! /usr/bin/env python
#
# bypy.py ---
#
# Filename: bypy.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Mon Sep  4 14:05:16 2017 (+0800)
#

# Change Log:
#
#

import sys
import os
import json
from six.moves import _thread
import time
import zipfile

from slackbot.bot import plugin_init
from slackbot.bot import respond_to
from slackbot.bot import tick_task

import subprocess

import difflib


DOWNLOAD_DIR='/mnt/mmc/mi/'
VIDEO_DIR='/mnt/mmc/mi/Videos'

class BYPY(object):
    DOWNLOAD_SESSIONS_DIR = '/mnt/mmc/database/bypy/'
    DOWNLOAD_SESSIONS = os.path.join(DOWNLOAD_SESSIONS_DIR, 'bypy.json')
    DOWNLOAD_TAG = 'downloads'
    UPLOAD_TAG = 'uploads'
    def __init__(self, message):
        self._downlist = []
        self._uploadlist = []
        self._sessions = {}
        self._message = message
        if not os.path.exists(BYPY.DOWNLOAD_SESSIONS_DIR):
            os.mkdir(BYPY.DOWNLOAD_SESSIONS_DIR)
        if os.path.exists(BYPY.DOWNLOAD_SESSIONS):
            self._sessions = json.load(open(BYPY.DOWNLOAD_SESSIONS, 'r'))
        self.__first_start()

    def __notify(self, msg):
        self._message.send_to('werther0331', msg)

    def __first_start(self):
        # list remote path

        if self._sessions == {}:
            return

        downlist = self._sessions.get(BYPY.DOWNLOAD_TAG, [])
        for l in downlist:
            remotepath = l['remotepath']
            localpath = l['localpath']
            self.__update_sessions(BYPY.DOWNLOAD_TAG, 'add', remotepath, localpath)
            _thread.start_new_thread(self.__download_file, (remotepath, localpath))

        uploadlist = self._sessions.get(BYPY.UPLOAD_TAG, [])
        for l in uploadlist:
            remotepath = l['remotepath']
            localpath = l['localpath']
            self.__update_sessions(BYPY.DOWNLOAD_TAG, 'add', remotepath, localpath)

    def __download_file(self, remotepath, localpath):
        # localpath always is directory
        basename = os.path.basename(remotepath)
        tmpfile = os.path.join(localpath, basename + '.tmp')
        p = subprocess.Popen('python /usr/local/bin/bypy --config-dir=/root/.bypy/ download {} {}'.format(remotepath, tmpfile), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while p.poll() == None:
            self.__notify(p.stdout.readline())
            time.sleep(1)
        self.__notify(p.stdout.read())
        retcode = p.returncode
        if retcode == 0:
            # download success
            os.rename(tmpfile, os.path.join(localpath, basename))
            self.__notify('bypy download {} to {} success'.format(remotepath, localpath))
        else:
            self.__notify('bypy download {} failed'.format(remotepath))

        self.__update_sessions(BYPY.DOWNLOAD_TAG, 'delete', remotepath, localpath)

    def __update_sessions(self, tag, method, remotepath, localpath):
        if method == 'add' and tag == BYPY.DOWNLOAD_TAG:
            self._downlist.append({'remotepath': remotepath, 'localpath': localpath})
        if method == 'delete' and tag == BYPY.DOWNLOAD_TAG:
            for i in range(0, len(self._downlist)):
                l = self._downlist[i]
                if l.get('remotepath', '') == remotepath \
                   and l.get('localpath', '') == localpath:
                    del self._downlist[i]

        if method == 'add' and tag == BYPY.UPLOAD_TAG:
            self._uploadlist.append({'remotepath': remotepath, 'localpath': localpath})
        if method == 'delete' and tag == BYPY.UPLOAD_TAG:
            for i in range(0, len(self._uploadlist)):
                l = self._uploadlist[i]
                if l.get('remotepath', '') == remotepath \
                   and l.get('localpath', '') == localpath:
                    del self._uploadlist[i]

        sessions = dict()
        sessions[BYPY.DOWNLOAD_TAG] = self._downlist
        sessions[BYPY.UPLOAD_TAG] = self._uploadlist
        json.dump(sessions, open(BYPY.DOWNLOAD_SESSIONS, 'w'))

    def download(self, t, remotepath):
        if t == 'video':
            localdir = VIDEO_DIR
        else:
            localdir = DOWNLOAD_DIR
        self.__update_sessions(BYPY.DOWNLOAD_TAG, 'add', remotepath, localdir)
        _thread.start_new_thread(self.__download_file, (remotepath, localdir))
        return 'bypy start downloading {} to {}'.format(remotepath, localdir)

    def list_downloads(self):
        #self.__notify('{}'.format(self._downlist))
        return '{}'.format(self._downlist)

def unzip(zippath, dest):
    zippath = zippath
    fullunzipdirname = dest
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


_enable = False
_bypy = None

@plugin_init
def init_bypy(config):
    global _enable
    global _anywhere

    _enable = config.get('enable', False)

@tick_task
def bypy_tick(message):
    global _bypy
    if _bypy == None and _enable:
        _bypy = BYPY(message)

@respond_to(r'bypy (.*)')
def bypy_command(message, rest):
    if _bypy == None:
        message.reply('bypy Not enabled')

    command_list = ['ls', 'download', 'video']
    argv = ['bypy'] + rest.split()
    print("{}".format(argv))
    command = argv[1]
    c = difflib.get_close_matches(command, command_list)
    if c :
        command = c[0]
    if command == 'ls':
        ret = _bypy.list_downloads()
        message.reply(ret)
        return

    if command == 'download':
        if argv[2] == None:
            message.reply('Usage: bypy download [remotepath]')
            return

        ret = _bypy.download(command, argv[2])
        message.reply(ret)

    if command == 'video':
        if argv[2] == None:
            message.reply('Usage: bypy video [remotepath]')
            return

        ret = _bypy.download(command, argv[2])
        message.reply(ret)
