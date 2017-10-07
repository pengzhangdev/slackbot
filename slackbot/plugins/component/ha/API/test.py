#! /usr/bin/env python
#
# test.py ---
#
# Filename: test.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Thu Sep 28 21:31:17 2017 (+0800)
#

# Change Log:
#
#

import remote

api = remote.API('http://192.168.31.100', '')
print(remote.validate_api(api))

print('-- Available services:')
services = remote.get_services(api)
for service in services:
    print(service['services'])

print('\n-- Available events:')
events = remote.get_event_listeners(api)
for event in events:
    print(event)

print('\n-- Available entities:')
entities = remote.get_states(api)
for entity in entities:
    print(entity.entity_id)
    print(entity.attributes.get('status', entity.state))
    #print(entity)

print('\n-- vacuum.xiaomi_vacuum_cleaner state:')
entry = remote.get_state(api, 'vacuum.xiaomi_vacuum_cleaner')
print(entry)

print('\n-- history of all entiites: ')

entities = remote.get_histories(api)
for entity in entities:
    print(entity)

print('\n-- history of vacuum.xiaomi_vacuum_cleaner')
histories = remote.get_history(api, 'vacuum.xiaomi_vacuum_cleaner')
for item in histories:
    print(item)

import sys
sys.exit(1)

print('\n-- update vacuum.xiaomi_vacuum_cleaner state:')
domain='vacuum'
name = 'vacuum.xiaomi_vacuum_cleaner'
remote.call_service(api, domain, 'turn_on', {'entity_id': '{}'.format(name)})
import time
time.sleep(20)
entry = remote.get_state(api, 'vacuum.xiaomi_vacuum_cleaner')
print(entry)
remote.call_service(api, domain, 'turn_off', {'entity_id': '{}'.format(name)})
time.sleep(20)
entry = remote.get_state(api, 'vacuum.xiaomi_vacuum_cleaner')
print(entry)

