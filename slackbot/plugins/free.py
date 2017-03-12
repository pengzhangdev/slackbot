#! /usr/bin/env python
#
# free.py ---
#
# Filename: free.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Mar 12 11:26:41 2017 (+0800)
#

# Change Log:
#
#

import time
import json
import os
import random
import gc

from slackbot.bot import tick_task
from slackbot.bot import plugin_init

next_time = time.time() + 30 * 60

@plugin_init
def init_free(config):
    pass

@tick_task
def free_worker(message):
    global next_time
    now = time.time()
    if now < next_time:
        return

    next_time = now + 30 * 60 * 2
    gc.collect()
    print("After GC")
