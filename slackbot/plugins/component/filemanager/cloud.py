#! /usr/bin/env python
#
# cloud.py ---
#
# Filename: cloud.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Fri Oct 20 20:01:41 2017 (+0800)
#

# Change Log:
#
#

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    import utils.browser as b
else:
    from ...utils import browser as b

import sys
import os
import urllib
import urllib2
import cookielib
import requests
import json
from six.moves import _thread, queue
import time
import contextlib
import six
import threading
import logging

import uptimerobot

Lock = threading.Lock()
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

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

class Cloud(object):
    """Clound API to herokuapp"""
    _instance = None
    _inited = False
    _BASE_URL = "http://pyfile.herokuapp.com/"
    _SESSION = '/mnt/mmc/database/cloud/cloud.json'
    #_SESSION = '/tmp/cloud.json'
    _SESSION_TAG = 'cloud'
    def __init__(self):
        if Cloud._inited:
            return

        Cloud._inited = True
        _LOGGER.info("Init singleton Cloud")
        self._pool = WorkerPool(self.__job_thread, nworker=1)
        self._pool.start()
        self._uploadlist = []
        self._sessions = {}
        self._monitor = uptimerobot.get_monitor(Cloud._BASE_URL)
        if os.path.exists(Cloud._SESSION):
            self._sessions = json.load(open(Cloud._SESSION, 'r'))
            #self._uploadlist = self._sessions.get(Cloud._SESSION_TAG, [])
        _thread.start_new_thread(self.__first_start, ())

    def __new__(cls, *args, **kw):
        if not cls._instance:
            try:
                Lock.acquire()
                if not cls._instance:
                    cls._instance = super(Cloud, cls).__new__(cls, *args, **kw)
            finally:
                Lock.release()
        return cls._instance

    def __first_start(self):
        # read sessions and upload again

        if self._sessions == {}:
            return

        uploadlist = self._sessions.get(Cloud._SESSION_TAG, [])
        _LOGGER.debug(uploadlist)
        for u in uploadlist:
            path = u['localpath']
            self.__update_sessions('add', path)
            _LOGGER.info("first init upload {} start".format(path))
            self.__upload_file(u['localpath'], Cloud._BASE_URL)
            _LOGGER.info("first init upload {} success".format(path))
            self.__update_sessions('delete', path)
        _LOGGER.debug("done first init")
        self._pool.add_task(('monitor', ''))

    def __update_sessions(self, method, filepath):
        if method == 'add':
            self._uploadlist.append({'localpath': filepath})
        if method == 'delete':
            try:
                for i in range(0, len(self._uploadlist)):
                    l = self._uploadlist[i]
                    if l.get('localpath', '') == filepath:
                        del self._uploadlist[i]
            except:
                pass

        sessions = dict()
        sessions[Cloud._SESSION_TAG] = self._uploadlist
        json.dump(sessions, open(Cloud._SESSION, 'w'))

    def list(self):
        """list remote file"""
        response = ''
        itemlist = dict()

        with b.browser_base_urlopen(Cloud._BASE_URL) as f:
            try:
                itemlist = json.load(f)
            except:
                _LOGGER.exception('Cloud list failed to convert to json')

        return itemlist.get('files', [])

    def __upload_file(self, filename, url):
        import poster
        poster.streaminghttp.register_openers()
        with open(filename, 'rb') as f:
            datagen, headers = poster.encode.multipart_encode({'file': f})
            _LOGGER.debug("upload url: {}".format(url))
            request = urllib2.Request(url.encode('utf-8'), datagen, headers)
            resp = None
            try:
                resp = urllib2.urlopen(request)
            except urllib2.HTTPError as error:
                print(error)
                print(error.fp.read())

        try:
            buffer = resp.read()
            rest = json.loads(buffer)
        except:
            _LOGGER.exception('Failed to convert to json: {}'.format(buffer))
            rest = dict()
            return (False, 'Failed to upload to remote')

        return (True, rest.get('files')[0])

    def upload(self, filepath):
        """upload file to remote"""
        self.__update_sessions('add', filepath)
        result, info = self.__upload_file(filepath, Cloud._BASE_URL)
        self.__update_sessions('delete', filepath)

        if result == False:
            _LOGGER.error(info)
            return (False, info)

        self._pool.add_task(('monitor', ''))
        _LOGGER.debug("resume uptime robot")
        self._monitor.resume()
        return (True, info.get('url'))

    def __delete_file(self, filename, url):
        req = urllib2.Request(url)
        req.get_method = lambda:'DELETE'
        try:
            resp = urllib2.urlopen(req)
        except:
            _LOGGER.error('{}'.format(resp.read()))
            _LOGGER.exception('Failed to DELETE {}'.format(url))

        _LOGGER.debug('{}'.format(resp.read()))

    def delete(self, filename):
        """delete file remotely"""
        files = self.list()
        for f in files:
            if filename == f.get('name', ""):
                self.__delete_file(filename, f.get('delete_url', ''))
                return True
        return False

    def __job_thread(self, msg):
        _LOGGER.debug("job thread")
        command = msg[0]

        _LOGGER.debug('command : {}'.format(command))
        if command == 'monitor':
            files = self.list()
            if files != []:
                _LOGGER.debug("Waiting for timeout")
                time.sleep(10*60)
                self._pool.add_task(('monitor', ''))
            else:
                _LOGGER.debug("stop uptimerobot and quit")
                self._monitor.pause()
                return

if __name__ == '__main__':
    import sys
    logging.basicConfig()
    _LOGGER.setLevel(logging.DEBUG)
    cloud = Cloud()
    if sys.argv[1] == 'list':
        print(cloud.list())
    if sys.argv[1] == 'upload':
        print(cloud.upload(sys.argv[2]))
        time.sleep(20*60)
        cloud.delete(sys.argv[2])
        time.sleep(20*60)
    if sys.argv[1] == 'delete':
        print(cloud.delete(sys.argv[2]))
