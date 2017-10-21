#! /usr/bin/env python
#
# uptimerobot.py ---
#
# Filename: uptimerobot.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Oct 21 15:43:29 2017 (+0800)
#

# Change Log:
#
#

import sys
import os
import requests
import base64
import logging
import time
import json

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

_API_KEY = base64.b64decode('dTIyNDY0NC0zNDJmNWIxNGYxYTNjNjMyMGU2NjczNzQK')[:-1]

class Monitor(object):
    """Monitor item for uptimerobot"""
    _STATUS_PAUSE = 0
    _STATUS_RESUME = 1
    _STATUS_RUNNING = 2
    def __init__(self, id, name, url):
        self._id = id
        self._name = name
        self._url = url

    def pause(self):
        url = "https://api.uptimerobot.com/v2/editMonitor"

        payload = "api_key={}&format=json&id={}&status=0".format(_API_KEY, self._id)   # 0 for pause, 1 for resume (in seconds)
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache"
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        _LOGGER.debug(response.text)
        if json.loads(response.text)['stat'] == 'ok':
            return True
        return False

    def resume(self):
        url = "https://api.uptimerobot.com/v2/editMonitor"

        payload = "api_key={}&format=json&id={}&status=1".format(_API_KEY, self._id)   # 0 for pause, 1 for resume (in seconds)
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache"
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        _LOGGER.debug(response.text)
        if json.loads(response.text)['stat'] == 'ok':
            return True
        return False

    def status(self):
        url = "https://api.uptimerobot.com/v2/getMonitors"

        payload = "api_key={}&format=json&logs=1".format(_API_KEY)
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache"
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        _LOGGER.debug(response.text)
        json_dict = json.loads(response.text)
        for m in json_dict.get('monitors', []):
            if m.get('id') == self._id:
                return m.get('status')


def get_monitor(u):
    """get the monitor matches the url"""
    url = "https://api.uptimerobot.com/v2/getMonitors"

    payload = "api_key={}&format=json&logs=1".format(_API_KEY)
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'cache-control': "no-cache"
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    _LOGGER.debug(response.text)
    json_dict = json.loads(response.text)
    for m in json_dict.get('monitors', []):
        _LOGGER.debug("url1 {} url2 {}".format(m.get('url'), u))
        if m.get('url') == u:
            _LOGGER.debug("Matched")
            return Monitor(m.get('id'), m.get('name'), m.get('url'))


if __name__ == '__main__':
    import sys
    logging.basicConfig()
    _LOGGER.setLevel(logging.DEBUG)
    monitor = get_monitor("http://pyfile.herokuapp.com/")
    _LOGGER.debug('status {}'.format(monitor.status()))
    _LOGGER.debug('pause')
    monitor.pause()
    time.sleep(60)
    _LOGGER.debug('status {}'.format(monitor.status()))
    _LOGGER.debug('resume')
    monitor.resume()
    time.sleep(60)
    _LOGGER.debug('status {}'.format(monitor.status()))
    monitor.pause()
