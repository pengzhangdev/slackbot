#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# anywhere.py ---
#
# Filename: anywhere.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Mon Jul 24 13:37:15 2017 (+0800)
#

# Change Log:
#
#

import urllib
import urllib2
import cookielib
import requests
import json
from six.moves import _thread
import time
from slackbot.utils import download_file

class SendAnywhere (object):
    API_ENDPOINTS = "https://send-anywhere.com"
    RESPONSE_CODE = {
        200:"OK",
        400:"Bad Request. Invalid request query string.",
        403:"Bad Request. Invalid request query string.",
        404:"Not Found. Invalid key",
        429:"Too Many Request. To keep the amount of spam on Send Anywhere as low as possible.",
        500:"Internal Server Error. Something went wrong on our side. We're very sorry."
    }

    def __init__(self, api_key):
        self.cookie = cookielib.CookieJar()
        self.handler = urllib2.HTTPCookieProcessor(self.cookie)
        self.opener = urllib2.build_opener(self.handler)
        self.api_key = api_key
        self.__update()

    def __update(self):
        request_url = "https://send-anywhere.com/web/v1/device?api_key={}&profile_name=miroute".format(self.api_key)
        response = self.opener.open(request_url)

    def __upload_file(self, url, filename, timeout):
        files = {'file': open(filename, 'rb')}
        try:
            response = requests.post(url, files=files, timeout=timeout)
        except requests.exceptions.Timeout:
            print "Timeout waiting for post"

    def send(self, filename):
        key_api_url = "{}/web/v1/key".format(SendAnywhere.API_ENDPOINTS)
        response = self.opener.open(key_api_url)

        jdata = json.loads(response.read())
        print("share key: {}".format(jdata['key']))
        #print("{}".format(jdata))
        timeout = jdata['expires_time'] - jdata['created_time']
        _thread.start_new_thread(self.__upload_file, (jdata['weblink'], filename, timeout))
        #self.__upload_file(jdata['weblink'], filename, timeout)
        time.sleep(timeout)

    def receive(self, name, key):
        key_api_url = "{}/web/v1/key/{}".format(SendAnywhere.API_ENDPOINTS, key)
        response = self.opener.open(key_api_url)
        jdata = json.loads(response.read())
        print("{}".format(jdata))


if __name__ == '__main__':
    s = SendAnywhere("")
    s.send('Lonely.mp3')
    #s.receive(116133)
