# -*- coding: utf-8 -*-

import os
import json

DEBUG = False

PLUGINS = [
    'slackbot.plugins',
]

ERRORS_TO = None

# overwrite in config.json
API_TOKEN = '###token###'

'''
Setup a comma delimited list of aliases that the bot will respond to.

Example: if you set ALIASES='!,$' then a bot which would respond to:
'botname hello'
will now also respond to
'$ hello'
'''
ALIASES = ''

'''
If you use Slack Web API to send messages (with
send_webapi(text, as_user=False) or reply_webapi(text, as_user=False)),
you can customize the bot logo by providing Icon or Emoji. If you use Slack
RTM API to send messages (with send() or reply()), or if as_user is True
(default), the used icon comes from bot settings and Icon or Emoji has no
effect.
'''
# BOT_ICON = 'http://lorempixel.com/64/64/abstract/7/'
# BOT_EMOJI = ':godmode:'

'''Specify a different reply when the bot is messaged with no matching cmd'''
DEFAULT_REPLY = None

for key in os.environ:
    if key[:9] == 'SLACKBOT_':
        name = key[9:]
        globals()[name] = os.environ[key]

config_load = {}
with open("config.json", 'rb') as data:
    config_load.update(json.load(data))

# update from config.json
API_TOKEN = config_load.get('api_token', "None")
DEBUG = config_load.get("debug", False)
ERRORS_TO = config_load.get("errors_to", None)
DEFAULT_REPLY = config_load.get("default_reply", None)
plugin_configs = config_load.get("plugins", [])
PLUGIN_CONFIGS = {}
for c in plugin_configs:
    job = c.get('task', None)
    if job != None:
        PLUGIN_CONFIGS['%s' % (job)] = c


# try:
#     from slackbot_settings import *
# except ImportError:
#     try:
#         from local_settings import *
#     except ImportError:
#         pass

# # convert default_reply to DEFAULT_REPLY
# try:
#     DEFAULT_REPLY = default_reply
# except NameError:
#     pass
