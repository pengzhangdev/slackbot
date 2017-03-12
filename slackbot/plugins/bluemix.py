#! /usr/bin/env python
#
# bluemix.py ---
#
# Filename: bluemix.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Mar 12 11:35:27 2017 (+0800)
#

# Change Log:
#
#

import time
import json
import os
import urllib2
import cookielib
import random

from slackbot.bot import tick_task
from slackbot.bot import plugin_init

next_time = time.time()

bluemix_urls = list()
_enable = False

def _browser_base_urlopen(url):
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

@plugin_init
def init_bluemix(config):
    global _enable
    global bluemix_urls
    _enable = config.get('enable', False)
    for url in config.get('urls', []):
        bluemix_urls.append(url.get('url', ''))

@tick_task
def novel_worker(message):
    global next_time
    if next_time == -1:
        return

    next_time = -1
    for url in bluemix_urls:
        print("access {}".format(url))
        f = _browser_base_urlopen(url)
        buff = f.read()
