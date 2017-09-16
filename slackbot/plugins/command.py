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

import os
import sys
import traceback
import re
import urllib2
import cookielib
import BeautifulSoup
import base64
import json
import random
import contextlib
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.bot import plugin_init

import commands

DOWNLOAD_DIR='/mnt/mmc/mi/'

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

    def _create_list(self, buf, limits=5):
        result = list()
        soup = BeautifulSoup.BeautifulSoup(buf)
        objs = soup.findAll('dl', limit=limits)
        for obj in objs:
            #print('obj: {}'.format(obj))
            title = "*" + self._soup_strings(obj.findAll('a', limit=1)[0].contents).strip('<b>').strip('</b>') + "*"
            magnet = ""
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
                    #info = info + "\n**" + span.a.get('href', "None") + "**"
                    magnet = span.a.get('href', "None")
            result.append(title + "\n" + "_" + info + "_")
            result.append(magnet)
        return result

    def search(self, contents):
        self._enc = base64.b64encode(contents).strip('=').replace('/', '_').replace('+', '-')
        self._sort = CommandBT.SORT_HOT
        self._type = CommandBT.TYPE_ALL
        self._page = 1
        url = self._btdigg % (self._enc, self._page, self._sort, self._type)
        with  contextlib.closing(self._browser_base_urlopen(url)) as f:
            buf = f.read()
        return self._create_list(buf, limits=1)

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
        with  contextlib.closing(self._browser_base_urlopen(url)) as f:
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
        with  contextlib.closing(self._browser_base_urlopen(url)) as f:
            buf = f.read()
        return self._create_list(buf)

    @property
    def enabled(self):
        return self._enable


class CommandBot(object):
    def __init__(self, config):
        self._enable = config.get('enable', False)
        self._url = config.get('url', "https://raw.githubusercontent.com/pengzhangdev/slackbot/develop/")
        self._opener = None

    def update(self, path):
        url = self._url + path
        tmp_file = path + '.tmp'
        f = self._browser_base_urlopen(url)
        tmpf = open(tmp_file, 'wb')
        tmpf.write(f.read())
        f.close()
        tmpf.close()
        os.rename(tmp_file, path)

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

    def restart(self):
        python = sys.executable
        os.execl(python, python, * sys.argv)

    @property
    def enabled(self):
        return self._enable

class LogBot(object):
    DEFAULT_LINE_COUNT = 10
    LOG_DIRECTORY = '/root/ok6410/log/'
    def __init__(self, config):
        self.__linecount = config.get('line', LogBot.DEFAULT_LINE_COUNT)
    def getlog(self, name, linecount):
        count = 0;
        if linecount != 0:
            count = linecount
        else:
            count = self.__linecount
        with open(os.path.join(LogBot.LOG_DIRECTORY, name), 'r') as f:
            buff = f.readlines()
            total = len(buff)
            return ' '.join(buff[total - count:])

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
        if c.get('command', "") == 'bot':
            Objs['bot'] = CommandBot(c)
        if c.get('command', "") == 'log':
            Objs['log'] = LogBot(c)

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

@respond_to(r'bot (.*)')
@listen_to(r'bot (.*)')
def command_bot(message, rest):
    bot = Objs.get('bot', None)
    if bot == None:
        return

    if bot.enabled == False:
        return

    if message.get_user_id() != 'werther0331':
        message.reply('Permission deny, please contact to werther0331')

    contents = message.body.get('text', "")
    #_, command, rest = command_parser(contents, 3)
    argv = contents.split()
    command = argv[1]
    rest = ""
    if len(argv) > 2:
        rest = ' '.join(argv[2:])
    # print("{}".format(contents))
    just_exit = False
    try:
        if command == 'update':
            for r in rest.split():
                print("update %s" % (r))
                bot.update(r)
            #bot.restart()
            just_exit = True # the SystemExit exception will be catched
        elif command == 'ls':
            command_rest = ""
            for r in rest.split():
                if r.startswith('-'):
                    command_rest = command_rest + " " + r
                    continue
                if not r.startswith('/'):
                    r = os.path.join(DOWNLOAD_DIR, r)
                command_rest = command_rest + " " + r
            message.reply('run command: {} {}'.format(command, command_rest))
            status, outputinfo = commands.getstatusoutput('{} {}'.format(command, command_rest))
            message.reply('command return {}\n{}'.format(status, outputinfo))
        elif command == 'video':
            # mv target to directory Videos
            t = os.path.join(DOWNLOAD_DIR, 'Videos')
            for r in rest.split():
                r = os.path.join(DOWNLOAD_DIR, r)
                message.reply('run command mv {} {}'.format(r, t))
                status, outputinfo = commands.getstatusoutput('mv {} {}'.format(r, t))
                message.reply('command return {}\n{}'.format(status, outputinfo))
        elif command == 'git':
            # git command , likely git pull
            message.reply('run command {} {}'.format(command, rest))
            status, outputinfo = commands.getstatusoutput('{} {}'.format(command, rest))
            message.reply('command return {}\n{}'.format(status, outputinfo))
            just_exit = True
        else:
            message.reply('run command: {} {}'.format(command, rest))
            status, outputinfo = commands.getstatusoutput('{} {}'.format(command, rest))
            message.reply('command return {}\n{}'.format(status, outputinfo))
    except:
        tb = u'```\n{}\n```'.format(traceback.format_exc())
        message.reply('{}\n{}'.format(contents, tb))

    if just_exit:
        os._exit(1)


@respond_to(r'log (.*)')
@listen_to(r'log (.*)')
def log_bot(message, rest):
    logbot = Objs.get('log', None)
    if logbot == None:
        return
    contents = message.body.get('text', "")
    #_, command, rest = command_parser(contents, 3)
    argv = contents.split()
    count = 0
    f = argv[1]
    if len(argv) > 2:
        count = int(argv[2])
    message.reply(logbot.getlog(f, count))
