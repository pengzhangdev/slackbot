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
import time

EXTERNAL_PATH = '/mnt/mmc/mi/baidupan/Ebook_dup/'
DB_DIR  = '/mnt/mmc/database/bookshelf/'

class BookShelf(object):
    BOOKSHELFDATABASE = os.path.join(DB_DIR, 'bookshelf.db')
    def __init__(self):
        if not os.path.exists(DB_DIR):
            os.mkdir(DB_DIR)
        try:
            self._bookshelf = json.load(BookShelf.BOOKSHELFDATABASE)
        except:
            self._bookshelf = {}
        self.__books = {}

    def __add_to_database(self, metadata, path):
        """
        json format:
        {
        "time":"xxxx",
        "books": [
        {
        "xxx": [
        {"path": "yyyy"}
        ]
        },
        {
        "xxx": [
        {"path": "yyyy"}
        ]
        }
        ]
        }
        """
        bookname = metadata
        bookpath = path
        print 'add {} == {}'.format(bookname, bookpath)
        if bookname in self.__books:
            self.__books[bookname].append({"path": bookpath})
        else:
            self.__books[bookname] = [{"path": bookpath}]

    def __save_to_disk(self):
        self._bookshelf['time'] = time.time()
        self._bookshelf['books'] = self.__books
        json.dump(self._bookshelf, open(BookShelf.BOOKSHELFDATABASE, 'w'), ensure_ascii=False)

    def start_index(self):
        pathlist = []
        if self._bookshelf != {}:
            self.__books = self._bookshelf.get('books', None)
        if self.__books != None:
            for bookpath in  self.__books.values():
                pathlist.append(bookpath.get('path', None))

        for root, dirs, fpaths in os.walk(EXTERNAL_PATH):
            for name in fpaths:
                bookp = os.path.join(root, name)
                if bookp in pathlist :
                    continue
                if self.is_ebook(bookp):
                    self.__add_to_database(self.parse_file(bookp), bookp)
        self.__save_to_disk()

    def is_ebook(self, path):
        if path.endswith('.epub') or path.endswith('.mobi'):
            return True

        return False

    def __get_ebook_info(self, path):
        if path.endswith('.epub'):
            book = epub.read_epub(path)
            return '{}:{}'.format(book.get_metadata('DC', 'title')[0][0].encode('utf-8'),book.get_metadata('DC', 'creator')[0][0].encode('utf-8'))
        elif path.endswith('.mobi'):
            book = mobi.Mobi(path)
            book.parse()
            #print 'Failed to parse ' + path
            #return (book.title(), book.author())
            return '{}:{}'.format(book.title(), book.author())

    def parse_file(self, path):
        if self.is_ebook(path):
            try:
                ret = self.__get_ebook_info(path)
            except:
                ret = os.path.basename(path)
            return ret
                


if __name__ == '__main__':
	shelf = BookShelf()
	shelf.start_index()
