#! /usr/bin/env python
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
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.bot import plugin_init

class CommandBT(object):
    def __init__(self, config):
        self._enable = config.get('enable', False)
        self._last_requests = None

    def search(self, contents):
        pass

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

    message.reply('command: bt %s %s' % (command, rest))
