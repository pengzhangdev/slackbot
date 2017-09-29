#! /usr/bin/env python
#-*- coding:utf-8 -*-
#
# movie.py ---
#
# Filename: movie.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Fri Sep 29 13:25:41 2017 (+0800)
#

# Change Log:
#
#

import utils.browser as b
from utils.singleton import Singleton

from BeautifulSoup import BeautifulSoup

import datetime
import time
import logging
import sys
import os

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)



class dysfz(Singleton):
    """"""
    IGNORE_LIST='save/dysfz_ignore.txt'
    def __init__(self):
        self._url = 'http://www.dysfz.cc/'
        self.ignore_list = []
        self._load_ignore_list()

    def _load_ignore_list(self):
        if not os.path.exists(dysfz.IGNORE_LIST):
            return
        with open(dysfz.IGNORE_LIST, 'r') as f:
            for l in f.readlines():
                self.ignore_list.append(l[:-1])

    def _save_ignore_list(self):
        with open(dysfz.IGNORE_LIST, 'w') as f:
            f.write('\n'.join(self.ignore_list) + '\n')

    def _create_soup(self):
        buff = ""
        with b.browser_base_urlopen(self._url) as f:
            buff = f.read()

        return BeautifulSoup(buff)

    def _get_movie_list(self):
        """MOVEL (name, movie_url, db_url)"""
        movie_list = []
        lis = self._soup.findAll('li')
        _LOGGER.debug('{}'.format(lis))
        for li in lis:
            db = li.find(attrs={'class':'dbscore'})
            if not db:
                continue
            dbscore = float(db.b.string)
            if dbscore < 7:
                continue

            _LOGGER.debug('dbscore: {}'.format(dbscore))
            _LOGGER.debug('{}'.format(li.p.span.string))

            today = datetime.datetime.now().strftime('%Y-%m-%d')
            #if today != li.p.span.string:
            #    continue

            movie_name = '{}({})'.format(li.h2.a.string.encode('utf-8'), dbscore)
            movie_url = li.h2.a['href']
            db_url = li.p.find(attrs={'rel':'nofollow', 'target':'_blank'})['href']

            if db_url in self.ignore_list:
                continue

            _LOGGER.debug('{}\n{}\n{}'.format(movie_name, movie_url, db_url))
            movie_list.append((movie_name, movie_url, db_url))
            self.ignore_list.append(db_url)

        return movie_list

    def refresh(self):
        self._soup = self._create_soup()
        contents = self._get_movie_list()
        if len(contents) != 0:
            self._save_ignore_list()
        return contents


if __name__ == '__main__':
    logging.basicConfig()
    m = dysfz()
    items = m.refresh()
    for (name, url, db) in items:
        print('{}\n{}\n{}\n'.format(name, url, db))
    sys.exit()
