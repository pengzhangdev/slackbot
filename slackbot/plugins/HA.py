#! /usr/bin/env python
#
# HA.py ---
#
# Filename: HA.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Oct  7 19:39:46 2017 (+0800)
#

# Change Log:
#
#

from component.ha.MiVacuum import MiVacuum
import time
import difflib
import datetime
import logging

_LOGGER = logging.getLogger(__name__)

class HAConfig(object):
    """HAConfig"""

    def __init__(self):
        self._nextTime = {}
        self._configs = {}
        self._objects = {}

    def addConfig(self, key, obj, config):
        self._configs[key] = config
        self._objects[key] = obj
        self._nextTime[key] = 0

    def updateNextTime(self, key, nextTime):
        self._nextTime[key] = nextTime

    def checkTime(self, key, t):
        # 'weekday':'1,3,5'
        # 'time': '15:00'
        # 'interval': '60'
        config = self._configs[key]
        now = datetime.datetime.now()
        _LOGGER.debug('{}'.format(config))
        if 'weekday' in config:
            weeks = config['weekday'].encode('utf-8').split(',')
            week = str(now.isoweekday())
            _LOGGER.debug("week = {}, weeks = {}".format(week, weeks))
            if week not in weeks:
                return False

        _LOGGER.debug("t = {}, self._nextTime = {}".format(t, self._nextTime[key]))
        if t > self._nextTime[key] and self._nextTime[key] != 0:
            self._nextTime[key] = config.get('interval', 30*60) + time.time()
            return True

        if 'time' in config:
            year_str = now.strftime("%Y-%m-%d")
            time_str = year_str + ' ' + config['time']
            timeStamp = time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M"))
            _LOGGER.debug("abs time({}) stamp: {}".format(time_str, timeStamp))
            if t < timeStamp:
                self._nextTime[key] = timeStamp
            else:
                self._nextTime[key] = timeStamp + 24*60*60

        return False

    def getObject(self, key):
        return self._objects[key]

    @property
    def keys(self):
        return self._objects.keys()


from slackbot.bot import tick_task
from slackbot.bot import plugin_init
from slackbot.bot import respond_to

haconfig = HAConfig()

@plugin_init
def init_HA(config):
    global haconifg
    debug = config.get('debug', False)
    if debug :
        _LOGGER.setLevel(logging.DEBUG)
        logging.getLogger('MiVacuum').setLevel(logging.DEBUG)
    miVacuum = MiVacuum()
    miConfig = config.get('MiVacuum', '')
    miVacuum.update_config(miConfig)
    haconfig.addConfig('mivacuum', miVacuum, miConfig)

def guess(key, key_list):
    c = difflib.get_close_matches(key, key_list)
    if c :
        return c[0]
    return key

@tick_task
def HA_worker(message):
    global haconfig
    now = time.time()
    for key in haconfig.keys:
        if haconfig.checkTime(key, now):
            obj = haconfig.getObject(key)
            if hasattr(obj, 'automation'):
                obj.automation()

@respond_to(r'ha (.*)')
def ha_command(message, rest):
    global haconfig
    argv = message.body.get('text', "").split()

    domain_list = ['mivacuum']
    domain = argv[1]
    domain = guess(domain, domain_list)

    if domain == 'help':
        message.reply('ha mivacuum <start|stop|locate|status|suspend|resume>')
    if domain in haconfig.keys:
        obj = haconfig.getObject(domain)
        command_list = ['start', 'stop', 'locate', 'status', 'suspend', 'resume']
        command = argv[2]
        command = guess(command, command_list)
        if command == 'start':
            obj.start()
        if command == 'stop':
            obj.stop()
        if command == 'locate':
            obj.locate()
        if command == 'status':
            stat = obj.state()
            message.reply("The status of MiVacuum is {}".format(stat))
        if command == 'suspend':
            obj.suspend(True)
        if command == 'resume':
            obj.suspend(False)
