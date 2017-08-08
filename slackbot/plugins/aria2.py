#! /usr/bin/env python
#
# aria2.py ---
#
# Filename: aria2.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Fri Aug  4 17:18:46 2017 (+0800)
#

# Change Log:
#
#

import uuid
import difflib
import commands

from slackbot.bot import plugin_init
from slackbot.bot import respond_to

import aria2c

DOWNLOAD_DIR = '/mnt/mmc/mi/'
UUID = uuid.uuid1()
@plugin_init
def init_aria2(config):
    global DOWNLOAD_DIR
    global UUID

    DOWNLOAD_DIR = config.get('dir', DOWNLOAD_DIR)
    UUID = config.get('token', UUID)
    # aria2.sh stop
    status, outputinfo = commands.getstatusoutput('slackbot/plugins/aria2.sh stop');
    print 'stop aria2: {}'.format(outputinfo)
    # aria2.sh -d $DOWNLOAD_DIR -s $UUID stop
    # aria2.sh start
    status, outputinfo = commands.getstatusoutput('slackbot/plugins/aria2.sh -d {} start'.format(DOWNLOAD_DIR))
    print 'start aria2: {}'.format(outputinfo)
    # aria2.sh -d $DOWNLOAD_DIR -s $UUID start
    aria2c.SECRET_TOKEN = UUID

@respond_to(r'aria (.*)')
def aria2_command(message, rest):
    global UUID

    command_lists = ['token', 'add', 'remove', 'forcerm', 'info',
                     'pause', 'resume', 'list', 'errors', 'stats',
                     'paused', 'stopped', 'sleep', 'wake',
                     'purge', 'clean']

    argv = ['aria'] + rest.split()
    print('{}'.format(argv))
    if len(argv) <= 1:
        message.reply('aria {}'.format(' '.join(command_lists)))
    command = argv[1]
    arguments = []
    try:
        for i in argv[2:]:
            if i.startswith('<'):
                arguments += [i[1:-1]]
    except Exception as e:
        pass
    options = {}
    c = difflib.get_close_matches(command, command_lists)
    if c :
        command = c[0]

    r = ""
    if command == 'token':
        r = UUID
    elif command == 'add':
        print 'add_item {}'.format(arguments)
        r = aria2c.add_items(arguments, options)
    elif command == 'remove':
        r = aria2c.remove_by_gid(arguments)
    elif command == 'forcerm':
        r = aria2c.forcerm_by_gid(arguments)
    elif command == 'info':
        r = aria2c.info_by_gid(arguments, options)
    elif command == 'preview':
        r = aria2c.preview_by_gid(arguments, options)
    elif command == 'pause':
        r = aria2c.pause_by_gid(arguments)
    elif command == 'resume':
        r = aria2c.resume_by_gid(arguments)
    elif command == 'list':
        r = aria2c.list_downloads('active')
    elif command == 'errors':
        r = aria2c.show_errors()
    elif command == 'stats':
        r = aria2c.show_stats()
    elif command == 'paused':
        r = aria2c.list_downloads('waiting')
    elif command == 'stopped':
        r = aria2c.list_downloads('stopped')
    elif command == 'sleep':
        r = aria2c.call_func('pauseAll')
    elif command == 'wake':
        r = aria2c.call_func('unpauseAll')
    elif command == 'purge':
        r = aria2c.call_func('purgeDownloadResult')
    elif command == 'clean':
        r = aria2c.clean()
    else:
        r = "Unknown command {}".format(command)

    message.reply('{} excute reply {}'.format(command, r))
