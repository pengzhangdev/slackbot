#! /usr/bin/env python
#
# movie.py ---
#
# Filename: movie.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Fri Sep 29 14:55:14 2017 (+0800)
#

# Change Log:
#
#

from dysfz import dysfz

import time
import threading

Lock = threading.Lock()

class MovieWoker(object):
    """"""
    _instance = None
    _inited = False
    def __init__(self):
        if MovieWoker._inited:
            return
        print("Init singleton MovieWoker")
        MovieWoker._inited = True
        self._interval = 6*60*60
        self._enable = False
        self._next_wake_time = time.time()
        self._dysfz = dysfz()

    def __new__(cls, *args, **kw):
        if not cls._instance:
            try:
                Lock.acquire()
                if not cls._instance:
                    cls._instance = super(MovieWoker, cls).__new__(cls, *args, **kw)
            finally:
                Lock.release()
        return cls._instance

    def update_config(self, config):
        # read from config
        self._interval = config.get('interval', 6*60*60)
        self._enable = config.get('enable', True)

    def on_tick(self, message):
        if not self._enable:
            print("movie is not enabled");
            return

        now = time.time()

        if now < self._next_wake_time:
            return

        self._next_wake_time = now + self._interval

        items = self._dysfz.refresh()
        for (name, url, db) in items:
            message.send_to('werther0331', '{}\n{}\n{}'.format(name, url, db))

    def stop(self):
        self._enable = False

    def start(self):
        self._enable = True


from slackbot.bot import tick_task
from slackbot.bot import plugin_init
from slackbot.bot import respond_to

@plugin_init
def init_movie(config):
    worker = MovieWoker()
    worker.update_config(config)

@tick_task
def movie_worker(message):
    worker = MovieWoker()
    worker.on_tick(message)

@respond_to(r'movie (.*)')
def movie_command(message, rest):
    argv = message.body.get('text', "").split()

    command = argv[1]

    if command == 'stop':
        worker = MovieWoker()
        worker.stop()
    if command == 'start':
        worker = MovieWoker()
        worker.start()

