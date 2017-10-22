#! /usr/bin/env python
#
# fm.py ---
#
# Filename: fm.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Oct 21 20:24:01 2017 (+0800)
#

# Change Log:
#
#

import sys
import difflib

from component.filemanager import FileManager

from slackbot.bot import plugin_init
from slackbot.bot import respond_to
from slackbot.bot import tick_task

_fm = None
_enable = False

def guess(key, key_list):
    c = difflib.get_close_matches(key, key_list)
    if c :
        return c[0]
    return key

def get_rest_args(body, arg):
    index = body.find(arg)
    rest = body[index:]
    return rest

@plugin_init
def init_fm(config):
    global _enable
    _enable = config.get('enable', False)

@tick_task
def fm_tick(message):
    global _fm
    global _enable
    if _fm == None and _enable:
        _fm = FileManager()

@respond_to(r'fm (.*)')
def fm_command(message, rest):
    global _fm
    global _enable

    if _fm == None:
        message.reply('FileManager is not enabled')

    body = message.body.get('text', "")
    argv = message.body.get('text', "").split()

    domain_list = ['cloud']
    domain = argv[1]
    domain = guess(domain, domain_list)

    if domain == 'help':
        message.reply('fm cloud <list|upload|info>')
    if domain == 'cloud':
        command_list = ['list', 'upload', 'info', 'remove']
        command = argv[2]
        command = guess(command, command_list)
        if command == 'list':
            files = _fm.cloudList()
            message.reply('\n '.join(files))
        if command == 'upload':
            fname = get_rest_args(body, argv[3])
	    print("upload fname")
            status, url = _fm.cloudUpload(fname)
            if status:
                message.reply("Upload Success {}".format(url))
            else:
                message.reply("Upload Failed")
        if command == 'info':
            fname = get_rest_args(body, argv[3])
            info = _fm.cloudFileInfo(fname)
            message.reply(', '.join(info))

        if command == 'remove':
            fname = get_rest_args(body, argv[3])
            res = _fm.cloudRemoveFile(fname)
            message.reply('remove {} {}'.format(fname, 'successfully' if res else 'failed'))
