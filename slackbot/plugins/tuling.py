#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# tuling.py ---
#
# Filename: tuling.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Wed Oct 12 19:54:46 2016 (+0800)
#

# Change Log:
#
#

import re
import requests
import json
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.bot import plugin_init

class TulingBot(object):
    def __init__(self, key, debug, enable):
        self.tuling_key = key
        self.debug = debug
        self.enable = enable

    def tuling_auto_reply(self, uid, msg):
        if self.tuling_key:
            url = "http://www.tuling123.com/openapi/api"
            user_id = uid.replace('@', '')[:30]
            # timeArray = time.strptime(a, "%Y-%m-%d %H:%M:%S")
            # timeStamp = int(time.mktime(timeArray))
            # keyParam = "86b1e78e44204f4e" + str(timeStamp) + self.tuling_key
            # md = md5.new()
            # md.update(keyParam)
            # aesKey = md.hexdigest()
            # print "aesKey length {}; {}".format(length(aesKey), aesKey)
            body = {'key': self.tuling_key, 'info': msg.encode('utf8'), 'userid': user_id}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            # print "request:{}; response{};".format(body, respond)
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
            elif respond['code'] == 200000:
                result = respond['url']
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                        k['article'] + "\t" + k['detailurl'] + "\n"
            else:
                result = respond['text'].replace('<br>', '  ')

            #print '    ROBOT:', result
            return result
        else:
            return u"知道啦"

tuling = None

@plugin_init
def init_tuling(config):
    global tuling
    enable = config.get('enable', False)
    debug = config.get('debug', False)
    api_key = config.get('api_key', '00')
    tuling = TulingBot(api_key, debug, enable)

@respond_to(r'(.*)')
@listen_to(r'(.*)')
def tulingbot(message, rest):
    global tuling
    if tuling.enable == False:
        return

    body = message.body
    uid = ""
    channel = body['channel']
    if channel.startswith('C') or channel.startswith('G'):
        if 'user' in body:
            uid = body['user']
        else:
            uid = body.get('username', "")
    else:
        uid = channel

    msg = body['text']
    re = tuling.tuling_auto_reply(uid, msg)
    message.reply(re)
