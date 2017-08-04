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

from slackbot.bot import plugin_init
from slackbot.bot import respond_to

import aria2c

DOWNLOAD_DIR = '/mnt/mmc/mi/'
UUID = uuid.uuid3()
@plugin_init
def init_aria2(config):
    global DOWNLOAD_DIR
    global UUID
    # aria2.sh stop
    # aria2.sh -d $DOWNLOAD_DIR -s $UUID stop
    # aria2.sh start
    # aria2.sh -d $DOWNLOAD_DIR -s $UUID start

    DOWNLOAD_DIR = config.get('dir', DOWNLOAD_DIR)
    UUID = config.get('token', UUID)

@respond_to(r'aria (.*)')
def aria2_command(message, rest):
    global UUID

    command_lists = ['']

    argv = ['aria'] + rest.split()
    print('{}'.format(argv))
    command = argv[1]
    c = difflib.get_close_matches(command, command_lists)
    if c :
        command = c[0]

    
