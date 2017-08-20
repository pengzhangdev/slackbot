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

if sys.argv[1].endswith('.epub'):

    book = epub.read_epub(sys.argv[1])
    print '{}:{}'.format(book.get_metadata('DC', 'title')[0][0].encode('utf-8'),book.get_metadata('DC', 'creator')[0][0].encode('utf-8'))

elif sys.argv[1].endswith('.mobi'):
    book = mobi.Mobi(sys.argv[1])
    book.parse()
    print '{}:{}'.format(book.title(), book.author())
