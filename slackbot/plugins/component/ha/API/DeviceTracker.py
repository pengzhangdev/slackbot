#! /usr/bin/env python
#
# member.py ---
#
# Filename: DeviceTracker.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Oct  8 13:50:42 2017 (+0800)
#

# Change Log:
#
#

import remote
import logging

_LOGGER = logging.getLogger(__name__)

class DeviceTracker(object):
    """DeviceTracker API"""
    HOME = "home"
    AWAY = "not_home"
    def __init__(self):
        self._api = remote.API("http://192.168.31.100", '')
        self._valid = str(remote.validate_api(self._api)) == 'ok'
        self._domain = 'device_tracker'

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

    def get_name(self, name):
        if not self._valid:
            return (False, "API Invalid")

        entry = remote.get_state(self._api, name)
        return entry.attributes.get('friendly_name', name)

if __name__ == '__main__':
    logging.basicConfig()
    _LOGGER.setLevel(logging.DEBUG)
    dt = DeviceTracker()
    print(dt.get_state('device_tracker.werther'))
    print(dt.get_name('device_tracker.werther'))
    print(dt.get_state('device_tracker.xiaohetdeiphone'))
    print(dt.get_name('device_tracker.xiaohetdeiphone'))
    print(dt.get_history('device_tracker.werther'))
    print(dt.get_history('device_tracker.xiaohetdeiphone'))
