#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# command.py ---
#
# Filename: command.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Oct 22 17:28:25 2016 (+0800)
#

# Change Log:
#
#

import re
import urllib2
import cookielib
import BeautifulSoup
import base64
import json
import random
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.bot import plugin_init

class CommandBT(object):
    SORT_RELATIVE = 0
    SORT_DATE = 1
    SORT_SIZE = 2
    SORT_FCOUNT = 3
    SORT_HOT = 4
    TYPE_ALL = 0
    TYPE_PROGRAM = 5
    TYPE_VIDEO = 2
    TYPE_BOOK = 4
    def __init__(self, config):
        self._enable = config.get('enable', False)
        self._last_requests = None
        self._btdigg = config.get("url", "http://btdigg.pw/search/%s/%d/%d/%d.html") # base64("string"), page, sort, type
        self._sort = CommandBT.SORT_RELATIVE
        self._type = CommandBT.TYPE_ALL
        self._page = 1
        self._enc = ""
        self._opener = None

    def _browser_base_urlopen(self, url):
        cookie_support= urllib2.HTTPCookieProcessor(cookielib.CookieJar())
        self._opener = urllib2.build_opener(cookie_support,urllib2.HTTPHandler)
        urllib2.install_opener(self._opener)
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
        self._opener.addheaders = [("User-agent",agent),("Accept","*/*"),('Referer','https://www.google.com')]
        res = self._opener.open(url)
        return res

    def _soup_strings(self, contents):
        result = ""
        for c in contents:
            if type(c) == BeautifulSoup.NavigableString:
                result += c
            if type(c) == BeautifulSoup.Tag:
                result += c.string
        return result

    def _create_list(self, buf):
        result = list()
        soup = BeautifulSoup.BeautifulSoup(buf)
        objs = soup.findAll('dl', limit=5)
        for obj in objs:
            #print('obj: {}'.format(obj))
            title = self._soup_strings(obj.findAll('a', limit=1)[0].contents).strip('<b>').strip('</b>')
            #print("title: %s" % (title))
            info = ""
            #print("span {}".format(obj.findAll('span', limit=6)))
            for span in obj.findAll('span', limit=6):
                s = self._soup_strings(span.contents).strip('<b>').strip('</b>')
                #print("span {}".format(span))
                #print("s: %s" % (s))
                if s != u'磁力链接':
                    info = info + s + ";"
                else:
                    info = info + "\nurl: " + span.a.get('href', "None")
            result.append(title + "\ninfo: " + info)
        return result

    def search(self, contents):
        self._enc = base64.b64encode(contents).strip('=')
        self._sort = CommandBT.SORT_RELATIVE
        self._type = CommandBT.TYPE_ALL
        self._page = 1
        url = self._btdigg % (self._enc, self._page, self._sort, self._type)
        f = self._browser_base_urlopen(url)
        buf = f.read()
        return self._create_list(buf)

    def search_with_sort(self, sort_string):
        if sort_string == "relative":
            self._sort = CommandBT.SORT_RELATIVE
        if sort_string == 'date':
            self._sort = CommandBT.SORT_DATE
        if sort_string == 'size':
            self._sort = CommandBT.SORT_SIZE
        if sort_string == 'filecount':
            self._sort = CommandBT.SORT_FCOUNT
        if sort_string == 'hot':
            self._sort = CommandBT.SORT_HOT
        url = self._btdigg % (self._enc, self._page, self._sort, self._type)
        f = self._browser_base_urlopen(url)
        buf = f.read()
        return self._create_list(buf)

    def search_with_type(self, type_string):
        if type_string == 'all':
            self._type = CommandBT.TYPE_ALL
        if type_string == 'video':
            self._type = CommandBT.TYPE_VIDEO
        if type_string == 'book':
            self._type = CommandBT.TYPE_BOOK

        url = self._btdigg % (self._enc, self._page, self._sort, self._type)
        f = self._browser_base_urlopen(url)
        buf = f.read()
        return self._create_list(buf)

    @property
    def enabled(self):
        return self._enable


Objs = dict()

def command_parser(commands, argc):
    """split commands in \s"""
    argv = commands.split()
    if len(argv) > argc:
        return argv[:argc-1] + [' '.join(argv[argc-1:])]
    return argv

@plugin_init
def init_command(config):
    if config.get('enable', False) == False:
        return

    for c in config.get("commands", {}):
        if c.get('command', "") == 'bt':
            Objs['bt'] = CommandBT(c)

@respond_to(r'bt [\s]*[a-zA-Z0-9]+ (.+)')
@listen_to(r'bt [\s]*[a-zA-Z0-9]+ (.+)')
def command_bt(message, rest):
    bt = Objs.get('bt', None)
    if bt == None:
        return

    if bt.enabled == False:
        return
    contents = message.body.get('text', "")
    _, command, rest = command_parser(contents, 3)

    result = list()
    if command == 'search':
        result = bt.search(rest)
    if command == 'sort':
        result = bt.search_with_sort(rest)
    if command == 'type':
        result = bt.search_with_type(rest)

    for r in result:
        message.reply(r)
