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
import urllib2
import cookielib
import random
import sys

from slackbot.bot import tick_task
from slackbot.bot import plugin_init
from slackbot.bot import respond_to

NovelSaved = dict()

class Novel(object):
    def __init__(self, url, mode):
        self._url = url
        self._soup = self._create_soup()
        self._contents = list()
        self._updated_contents = list()
        self._title = None
        self._mode = mode
        #self._update()

    def _browser_base_urlopen(self, url):
        opener = None
        cookie_support= urllib2.HTTPCookieProcessor(cookielib.CookieJar())
        opener = urllib2.build_opener(cookie_support,urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        user_agents = [
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
            'Opera/9.25 (Windows NT 5.1; U; en)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
            'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
            'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
            "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
            "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 ",
        ]
        agent = random.choice(user_agents)
        opener.addheaders = [("User-agent",agent),("Accept","*/*"),('Referer','https://www.google.com')]
        res = opener.open(url)
        return res

    def _update(self, count):
        if not self._title:
            self._title = self._get_title()
        self._update_novel_contents(count)

    def _create_soup(self):
        buff = ""
        try:
            #f = urlopen(self._url);
            print("url: %s" % (self._url))
            f = self._browser_base_urlopen(self._url)
            buff = f.read()
        except:
            time.sleep(1)
            #f = urlopen(self._url);
            f = self._browser_base_urlopen(self._url)
            buff = f.read()
        return BeautifulSoup(buff)

    def _get_title(self):
        obj = self._soup.findAll('h1', limit=1)
        return obj[0].string

    def _update_novel_contents(self, count = 0):
        global NovelSaved
        self._updated_contents = list()
        self._contents = list()
        update = False
        #obj = self._soup.findAll('table', cellspacing='1', cellpadding='0', limit=1)
        nlist = self._soup.findAll('dd')

        if NovelSaved.get(self.title, None) == None:
            update = True

        for l in nlist[12:]:
            if update:
                self._updated_contents.append("%s -.- %s%s" % (l.a.string, self._url, os.path.basename(l.a.get('href', ""))))

            if l.a.string == NovelSaved.get(self.title, ""):
                update = True

            if count != 0 and len(self._updated_contents) < count:
                continue

            if self._mode == "roam" and len(self._updated_contents) >= 1:
                return

        if update == False:
            #NovelSaved.pop(self.title)
            self._updated_contents.append("%s -.- %s%s"
                                          % (nlist[-1].a.string, self._url, os.path.basename(nlist[-1].a.get('href', ""))))

        #     if l.string not in self._cached_contents:
        #         self._updated_contents.append("%s -.- %s%s" % (l.string, self._url, l.get('href', "")))
        #     self._contents.append(l.string)
        # self._cached_contents = self._contents

    def refresh(self, count = 0):
        self._soup = self._create_soup()
        self._update(count)

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
    global novels
    now = time.time()
    if now < next_time:
        return

    next_time = now + _interval + random.randint(-30*60, 30*60)

    if time.strftime("%H") > 23 and time.strftime("%H ") < 6:
        return

    if len(novels) == 0:
        for s in _source_config:
            url = s.get('url', "")
            mode = s.get('mode', "")
            try:
                novels.append(Novel(url, mode))
            except Exception as e:
                print("{}".format(e))
                novels = []
                next_time = now + 10 * 60;
                t, v, tb = sys.exc_info()
                raise t, v, tb

    random.shuffle(novels)
    try:
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
                        time.sleep(1)
                else:
                    # first inited
                    # print("%s updtes:  %s" % (title, updated[-2]))
                    # print("First fetch")
                    message.send_to('werther0331', u'%s updates : %s' % (title, updated[-1]))
                    NovelSaved[title] = updated[-1].split('-.-')[0][:-1]
                break
            else:
                # print("No updates")
                pass

    except Exception as e:
        print("{}".format(e))
        next_time = now + 5*60
        raise e

    with open('save/novel.json', "w") as f:
        f.write(json.dumps(NovelSaved, ensure_ascii = False))

def command_parser(commands, argc):
    """split commands in \s"""
    argv = commands.split()
    if len(argv) > argc:
        return argv[:argc-1] + [' '.join(argv[argc-1:])]
    return argv

@respond_to(r'novel (.*)')
def novel_command(message, rest):
    global next_time
    global novels
    global NovelSaved

    argv = command_parser(message.body.get('text', ""), 4)
    command = ""
    rest = ""
    count = 0

    if len(argv) >= 2:
        command = argv[1]
    if len(argv) >= 3:
        rest = argv[2]

    if len(argv) == 4:
        count = int(argv[3])

    if command == "update":
        if len(rest) == 0:
            next_time = 0
        else:
            for novel in novels:
                if novel.title == rest:
                    novel.refresh(count)
                    updated = novel.latest_contents
                    if len(updated) != 0:
                        for u in updated:
                            message.send_to('werther0331', u'%s update : %s' % (rest, u))
                            NovelSaved[novel.title] = u.split('-.-')[0][:-1]
                            time.sleep(1)
                    break

    if command == "list":
        novel_lists = ""
        for novel in novels:
            novel_lists += novel.title + "\n"
        message.send_to('werther0331', u'%s' % (novel_lists))

    with open('save/novel.json', "w") as f:
        f.write(json.dumps(NovelSaved, ensure_ascii = False))

# def test_main():
#     nurl = 'http://www.23wx.com/html/55/55035/'
#     n = Novel(nurl, "roam")
#     print("title %s" % (n.title))

#     n.refresh()
#     print("title %s" % (n.title))
#     for i in n.latest_contents:
#         print("%s" % (i))

# if __name__ == '__main__':
#     test_main()
