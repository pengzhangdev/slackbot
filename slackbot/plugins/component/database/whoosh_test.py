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


from whoosh.index import create_in
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
