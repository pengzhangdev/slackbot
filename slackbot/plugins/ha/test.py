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
    print(entity)

