#! /usr/bin/env python
#
# whoosh_test.py ---
#
# Filename: whoosh_test.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Mon Oct 23 19:29:49 2017 (+0800)
#

# Change Log:
#
#

import os

from whoosh.index import create_in
from whoosh.index import exists_in
from whoosh.index import open_dir
from whoosh.fields import *

schema = Schema(title=TEXT(stored=True), path=ID(stored=True), author=TEXT, content=TEXT) # stored=True will show the result in results[0]
ix = create_in("indexdir", schema)
writer = ix.writer()
writer.add_document(title=u"First document", path=u"/a", author=u"Werther", content=u"This is the first document we've added!")
writer.add_document(title=u"Second document", path=u"/b", content=u"The second one is even more interesting!")
writer.commit()
from whoosh.qparser import QueryParser
with ix.searcher() as searcher:
    query = QueryParser("author", ix.schema).parse("werther")
    results = searcher.search(query)
    print results[0]

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser

class BookshelfDatabase(object):
    """BookshelfDatabase API"""
    _DATABASE_DIR = '/mnt/mmc/database/bookshelf'
    def __init__(self):
        ix = None
        # title (filename or title in db)
        # path  (relative path in /mnt/mmc/mi)
        # author (author of the file)
        # content (basename of file ; title; author)
        # fileid (hash of path)
        # date (file update time in string)
        #
        # when index, check whether file updated,
        #                using date AND fileid to get the item , if it not exists, update fileid with new info
        # when search, using content defaultly and merge result in path , show title and path to user
        schema = Schema(title=TEXT(stored=True), path=ID(stored=True), author=TEXT, content=TEXT, fileid=TEXT(unique=True), date=TEXT)
        if not os.path.exists(BookshelfDatabase._DATABASE_DIR):
            os.mkdir(BookshelfDatabase._DATABASE_DIR)
        if not exists_in(BookshelfDatabase._DATABASE_DIR):
            ix = create_in(BookshelfDatabase._DATABASE_DIR, schema)
        else:
            ix = open_dir(BookshelfDatabase._DATABASE_DIR)


    def add(self, title, path, content, fileid, date, author=None):
        pass

    def update(self, title, path, content, fileid, date, author=None):
        pass

    # check fileid AND date exists
    def exists(self, fileid, date):
        pass

    def search(self, content=None, author=None):
        pass
