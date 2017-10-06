#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# tts.py ---
#
# Filename: tts.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Sep 10 16:24:08 2017 (+0800)
#

# Change Log:
#
#
from slackbot.bot import plugin_init
from slackbot.bot import respond_to
from slackbot.bot import listen_to

from component.ttsdriver import TTS
from component.player import Player


tts_obj = None
player_obj = None

@plugin_init
def init_tts(config):
    global tts_obj
    global player_obj
    enable = config.get('enable', False)
    driver = config.get('driver', 'baidu')
    if enable:
        tts_obj = TTS(config, driver)
        player_obj = Player()
        player_obj.update_config(driver='mplayer')

@respond_to(r'tts (.*)')
@listen_to(r'tts (.*)')
def tts_command(message, rest):
    global tts_obj
    global player_obj

    message.reply("Starting to tts {}".format(rest))
    f = tts_obj.text2play(rest)
    player_obj.play(f)
