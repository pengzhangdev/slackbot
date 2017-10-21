#! /usr/bin/env python
#
# filemanager.py ---
#
# Filename: filemanager.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Oct 21 17:53:40 2017 (+0800)
#

# Change Log:
#
#

import cloud
import os

from common import FILEPATH_LOCAL

class FileManager(object):
    """FileManager to mange local and remote file"""
    def __init__(self):
        self._cloud = cloud.Cloud()

    def cloudUpload(self, path):
        if path.startswith('/'):
            return self._cloud.upload(path)[1]
        else:
            return self._cloud.upload(os.path.join(FILEPATH_LOCAL, path))[1]

    def cloudList(self):
        files = []
        filelists = self._cloud.list()
        for f in filelists:
            files.append(f.get('name', ''))

        return files

    def cloudFileInfo(self, filename):
        filelists = self._cloud.list()
        for f in filelists:
            if filename == f.get('name', ''):
                return (f.get('name'), f.get('size'), f.get('url'))

