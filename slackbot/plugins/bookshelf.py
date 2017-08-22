#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# ebookparser.py ---
#
# Filename: ebookparser.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sun Aug 20 21:24:52 2017 (+0800)
#

# Change Log:
#
#

from ebooklib import epub
from ebooklib import mobi

import sys
import os
import json

import sqlite3

# save
# https://github.com/DoTheEvo/ANGRYsearch/blob/master/angrysearch_update_database.py

# read
# https://github.com/DoTheEvo/ANGRYsearch/blob/master/angrysearch.py

EXTERNAL_PATH = '/mnt/mmc/mi/'

class BookShelf(object):
    BOOKSHELFDATABASE = os.path.join(EXTERNAL_PATH, 'bookshelf.db')
    def __init__(self):
        self._bookshelf = json.load(BookShelf.BOOKSHELFDATABASE)

    def __new_database(table):
        if os.path.exists(BookShelf.BOOKSHELFDATABASE):


def is_ebook(path):
    if path.endswith('.epub') or path.endswith('.mobi'):
        return True

    return False

def get_ebook_info(path):
    if path.endswith('.epub'):
        book = epub.read_epub(path)
        return '{}:{}'.format(book.get_metadata('DC', 'title')[0][0].encode('utf-8'),book.get_metadata('DC', 'creator')[0][0].encode('utf-8'))
    elif path.endswith('.mobi'):
        book = mobi.Mobi(path)
        book.parse()
        return '{}:{}'.format(book.title(), book.author())

def parse_file(path):
    if is_ebook(path):
        return get_ebook_info(path)


if __name__ == '__main__':
    print parse_file(sys.argv[1])
