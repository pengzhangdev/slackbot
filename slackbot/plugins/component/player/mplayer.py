#! /usr/bin/env python
#
# mplayer.py ---
#
# Filename: mplayer.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Fri Oct  6 20:33:33 2017 (+0800)
#

# Change Log:
#
#
import commands

class MPlayer(object):
    """"""
    def __init__(self):
        pass

    def play(self, filename):
        st, output = commands.getstatusoutput('mplayer -really-quiet -noconsolecontrols -volume 90 -speed 0.9 {}'.format(filename))
