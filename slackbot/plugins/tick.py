#! /usr/bin/env python
#
# tick.py ---
#
# Filename: tick.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Tue Oct 11 16:07:15 2016 (+0800)
#

# Change Log:
#
#

# -*- coding: utf-8 -*-

import time
from slackbot.bot import tick_task

count = 0
next_time=0
@tick_task
def hello(message):
    global count
    global next_time
    now = time.time()
    if now < next_time:
        return
    next_time = now + 5         # every 5 seconds
    message.send_to('werther0331', 'hello {}'.format(count))
    count += 1
