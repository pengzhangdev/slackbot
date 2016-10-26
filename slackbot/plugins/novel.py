#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# novel.py ---
#
# Filename: novel.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Wed Oct 12 09:52:37 2016 (+0800)
#

# Change Log:
#
#

import time
import json
import os
from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen

from slackbot.bot import tick_task
from slackbot.bot import plugin_init

NovelSaved = dict()

class Novel(object):
    def __init__(self, url, mode):
        self._url = url
        self._soup = self._create_soup()
        self._contents = list()
        self._updated_contents = list()
        self._title = ""
        self._mode = mode
        #self._update()

    def _update(self):
        self._title = self._get_title()
        self._update_novel_contents()

    def _create_soup(self):
        buff = ""
        try:
            f = urlopen(self._url);
            buff = f.read()
        except:
            time.sleep(1)
            f = urlopen(self._url);
            buff = f.read()
        return BeautifulSoup(buff)

    def _get_title(self):
        obj = self._soup.findAll('h3', limit=1)
        return obj[0].string.split(u'作者')[0]

    def _update_novel_contents(self):
        global NovelSaved
        self._updated_contents = list()
        self._contents = list()
        update = False
        obj = self._soup.findAll('table', cellspacing='1', cellpadding='0', limit=1)
        nlist = obj[0].findAll('a')

        if NovelSaved.get(self.title, None) == None:
            update = True

        for l in nlist[:-1]:

            if update:
                self._updated_contents.append("%s -.- %s%s" % (l.string, self._url, l.get('href', "")))

            if l.string == NovelSaved.get(self.title, ""):
                update = True

            if self._mode == "roam" and len(self._updated_contents) == 1:
                return

        if update == False:
            NovelSaved.pop(self.title)

        #     if l.string not in self._cached_contents:
        #         self._updated_contents.append("%s -.- %s%s" % (l.string, self._url, l.get('href', "")))
        #     self._contents.append(l.string)
        # self._cached_contents = self._contents

    def refresh(self):
        self._soup = self._create_soup()
        self._update()

    @property
    def title(self):
        return self._title

    @property
    def contents(self):
        return self._contents

    @property
    def latest_contents(self):
        return self._updated_contents


next_time = time.time() + 30    # wait for 30 seconds to start
novels = list()

_enable = False
_debug = False
_source_url = list()
_interval = 6*60*60
_source_config = list()

@plugin_init
def init_novel(config):
    global _enable
    global _debug
    global _source_url
    global _interval
    global NovelSaved
    global _source_config
    _enable = config.get('enable', False)
    _debug = config.get('debug', False)
    sources = config.get('sources', [])
    for source in sources:
        en = source.get('enable', False)
        if en == False:
            continue
        _source_config.append(source)
    _interval = config.get('interval', 6*60*60)
    with open("save/novel.json", 'rb') as data:
        if os.path.getsize('save/novel.json') > 0:
            NovelSaved.update(json.load(data))

@tick_task
def novel_worker(message):
    url = 'http://www.23wx.com/html/55/55035/'
    global next_time
    global _source_config
    global _interval
    global NovelSaved
    now = time.time()
    if now < next_time:
        return

    next_time = now + _interval
    if len(novels) == 0:
        for s in _source_config:
            url = s.get('url', "")
            mode = s.get('mode', "")
            novels.append(Novel(url, mode))

    for novel in novels:
        novel.refresh()
        title = novel.title
        updated = novel.latest_contents
        if len(updated) != 0:
            if len(updated) < 10:
                # print("%s updtes:  %s" % (title, updated[0]))
                # print("Novel updated")
                for u in updated:
                    message.send_to('werther0331', u'%s updates : %s' % (title, u))
                    NovelSaved[title] = u.split('-.-')[0][:-1]
            else:
                # first inited
                # print("%s updtes:  %s" % (title, updated[-2]))
                # print("First fetch")
                message.send_to('werther0331', u'%s updates : %s' % (title, updated[-1]))
                NovelSaved[title] = updated[-1].split('-.-')[0][:-1]
        else:
            # print("No updates")
            pass

    with open('save/novel.json', "w") as f:
        f.write(json.dumps(NovelSaved, ensure_ascii = False))

# def test_main():
#     nurl = 'http://www.23wx.com/html/55/55035/'
#     n = Novel(nurl)
#     print("title %s" % (n.title))
#     for i in n.latest_contents:
#         print("%s" % (i))

#     n.refresh()
#     print("title %s" % (n.title))
#     for i in n.latest_contents:
#         print("%s" % (i))

# if __name__ == '__main__':
#     test_main()
