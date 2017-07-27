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
import base64
from slackbot.bot import tick_task
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.bot import plugin_init
import ibotcloud

class TulingBot(object):
    def __init__(self, key, debug, enable):
        self.tuling_key = key
        self.debug = debug
        self.enable = enable

    def tuling_auto_reply(self, uid, msg):
        if self.tuling_key:
            url = "http://www.tuling123.com/openapi/api"
            user_id = base64.b64encode(uid)
            # print("user_id : %s" % (user_id))
            # user_id = uid.replace('@', '')[:30]
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


class XiaoIBot(object):
    def __init__(self):
        self.key = "0vMVot7Ej5vJ"
        self.secret = "xU7bqIhZlyXpavEcv6h8"
        self.ask_sessions = dict()
        self.signature_ask = None

    def xiaoi_auto_reply(self, uid, msg):
        user_id = base64.b64encode(uid)
        session = None
        if self.signature_ask == None:
            self.signature_ask = ibotcloud.IBotSignature(app_key=self.key,
                                                           app_sec=self.secret,
                                                           uri="/ask.do",
                                                           http_method="POST")
        if self.ask_sessions.has_key(user_id):
            session = self.ask_sessions.get(user_id)
        else:
            params_ask = ibotcloud.AskParams(platform="custom",
                                                   user_id=user_id,
                                                   url="http://nlp.xiaoi.com/ask.do",
                                                   response_format="xml")
            session = ibotcloud.AskSession(self.signature_ask, params_ask)
            self.ask_sessions[user_id] = session
        ret_ask = session.get_answer(msg)
        if ret_ask.http_status != 200 or ret_ask.http_body == "I dont know":
            return None
        #print "xiaoi: {}".format(ret_ask.http_body)
        return ret_ask.http_body

tuling = None
xiaoi = None

@plugin_init
def init_tuling(config):
    global tuling
    global xiaoi
    enable = config.get('enable', False)
    debug = config.get('debug', False)
    api_key = config.get('api_key', '00')
    tuling = TulingBot(api_key, debug, enable)
    xiaoi = XiaoIBot()

@respond_to(r'^[^a-zA-Z0-9]')
@listen_to(r'^[^a-zA-Z0-9]')
def tulingbot(message):
    global tuling
    global xiaoi
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
    #print "handle chat"
    #rep = xiaoi.xiaoi_auto_reply(uid, msg)
    #if rep == None:
    rep = tuling.tuling_auto_reply(uid, msg)
    message.reply(rep)

GREETED = False

@tick_task
def tuling_worker(message):
    global GREETED
    if not GREETED:
        GREETED = True
        message.send_to('werther0331', "Hello Master, I am here!")
