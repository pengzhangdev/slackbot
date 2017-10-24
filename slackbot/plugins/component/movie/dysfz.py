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

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    import utils.browser as b
else:
    from ...utils import browser as b

from BeautifulSoup import BeautifulSoup

import datetime
import time
import logging
import sys
import os
import re
import hashlib

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

def md5sum(contents):
    _LOGGER.debug(contents)
    hash = hashlib.md5()
    hash.update(contents)
    return hash.hexdigest()

class dysfz(object):
    """"""
    IGNORE_LIST='save/dysfz_ignore.txt'
    def __init__(self):
        self._url = 'http://www.dysfz.cc/{}?o=2'
        self.ignore_list = []
        self._load_ignore_list()

    def _load_ignore_list(self):
        if not os.path.exists(dysfz.IGNORE_LIST):
            return
        with open(dysfz.IGNORE_LIST, 'r') as f:
            for l in f.readlines():
                self.ignore_list.append(l[:-1])

    def _save_ignore_list(self):
        if len(self.ignore_list) > 50:
            self.ignore_list = self.ignore_list[15:]
        with open(dysfz.IGNORE_LIST, 'w') as f:
            f.write('\n'.join(self.ignore_list) + '\n')

    def _create_soup(self, url):
        buff = ""
        with b.browser_base_urlopen(url) as f:
            buff = f.read()

        return BeautifulSoup(buff)

    def _get_dbsccore(self, dburl):
        try:
            soup = self._create_soup(dburl)
        except:
            _LOGGER.exception("Failed to fetch {} ".format(dburl))
            return 0.0

        item = soup.find(attrs={'class':'ll rating_num'})
        dbscore = item.string
        _LOGGER.debug('{}'.format(dbscore))
        if dbscore:
            return float(dbscore)
        return 0.0

    def _get_movie_list(self, soup):
        """MOVEL (name, movie_url, db_url)"""
        movie_list = []
        lis = soup.findAll('li')
        _LOGGER.debug('{}'.format(lis))
        for li in lis:
            # db = li.find(attrs={'class':'dbscore'})
            # if not db:
            #     continue
            # dbscore = float(db.b.string)
            year = datetime.datetime.now().strftime('%Y')
            year = int(year)
            #if today != li.p.span.string:
            #    continue
            _LOGGER.debug('LI {}'.format(li))
            if li.h2 == None:
                continue
            if li.p.find(attrs={'rel':'nofollow', 'target':'_blank'}) == None:
                continue
            movie_url = li.h2.a['href']
            db_url = li.p.find(attrs={'rel':'nofollow', 'target':'_blank'})['href'].encode('utf-8')
            dbscore = self._get_dbsccore(db_url)
            movie_name = '{}({})'.format(li.h2.a.string.encode('utf-8'), dbscore)
            movie_title = li.h2.a.string.encode('utf-8')
            movie_hash = md5sum(movie_title+db_url)
            all_year = re.findall(r'【\d+】', movie_name)
            movie_year = year
            if len(all_year) > 0:
                movie_year = int(all_year[0][3:-3])
                _LOGGER.debug('movie_year: {}'.format(movie_year))

            if movie_hash in self.ignore_list:
                continue

            if dbscore < 7:
                continue

            if movie_year < year - 1:
                continue

            _LOGGER.debug('dbscore: {}'.format(dbscore))
            _LOGGER.debug('{}'.format(li.p.span.string))
            _LOGGER.debug('{}\n{}\n{}'.format(movie_name, movie_url, db_url))
            movie_list.append((movie_name, movie_url, db_url))
            self.ignore_list.append(movie_hash)

        return movie_list

    def refresh(self):
        soups = []
        contents = []
        for i in (1, 2, 3):
            url = self._url.format(i)
            _LOGGER.debug('url: {}'.format(url))
            try:
                soups.append(self._create_soup(url))
            except:
                _LOGGER.exception("Failed to fetch {}".format(url))
        for soup in soups:
            contents += self._get_movie_list(soup)
        if len(contents) != 0:
            self._save_ignore_list()
        return contents


if __name__ == '__main__':
    logging.basicConfig()
    _LOGGER.setLevel(logging.DEBUG)
    m = dysfz()
    items = m.refresh()
    for (name, url, db) in items:
        print('{}\n{}\n{}\n'.format(name, url, db))
    sys.exit()
