#! /usr/bin/env python
#
# vacuum.py ---
#
# Filename: vacuum.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Oct  7 15:59:52 2017 (+0800)
#

# Change Log:
#
#

import logging
import remote
import time

_LOGGER = logging.getLogger(__name__)

class Vacuum(object):
    """Vacuum API"""
    CHARGING='Charging'
    CLEANING='Cleaning'
    ERROR='Error'
    def __init__(self):
        self._api = remote.API('http://192.168.31.100', '')
        self._valid = str(remote.validate_api(self._api)) == 'ok'
        self._domain = 'vacuum'

    def start(self, name):
        if not self._valid:
            return (False, "API invalid")
        remote.call_service(self._api, self._domain, 'turn_on', {'entity_id' : '{}'.format(name)})

    def stop(self, name):
        if not self._valid:
            return (False, "API invalid")
        remote.call_service(self._api, self._domain, 'turn_off', {'entity_id' : '{}'.format(name)})

        return (True, "")

    def locate(self, name):
        if not self._valid:
            return (False, "API invalid")
        remote.call_service(self._api, self._domain, 'locate', {'entity_id' : '{}'.format(name)})

        return (True, "")

    def get_state(self, name):
        if not self._valid:
            return (False, "API Invalid")

        entry = remote.get_state(self._api, name)
        return entry.attributes.get('status', entry.state)

    def get_history(self, name):
        if not self._valid:
            return (False, "API Invalid")
        histories = remote.get_history(self._api, name)
        h = []
        # state : last_changed
        for history in histories:
            d = {'state': '{}'.format(history.state),
                 'date': '{}'.format(history.last_changed),
                 'status': '{}'.format(history.attributes.get('status', history.state))}
            h.append(d)
        return h

    def get_error(self, name):
        if not self._valid:
            return (False, "API Invalid")

        entry = remote.get_state(self._api, name)
        status = entry.attributes.get('status', entry.state)
        return entry.attributes.get('error', 'OK')

if __name__ == '__main__':
    logging.basicConfig()
    _LOGGER.setLevel(logging.DEBUG)
    v = Vacuum()
    print(v.get_state('vacuum.xiaomi_vacuum_cleaner'))
    print(v.get_history('vacuum.xiaomi_vacuum_cleaner'))
    print(v.get_error('vacuum.xiaomi_vacuum_cleaner'))
    v.locate('vacuum.xiaomi_vacuum_cleaner')
    #v.start('vacuum.xiaomi_vacuum_cleaner')
    #time.sleep(30)
    #print(v.get_state('vacuum.xiaomi_vacuum_cleaner'))
    #v.stop('vacuum.xiaomi_vacuum_cleaner')
