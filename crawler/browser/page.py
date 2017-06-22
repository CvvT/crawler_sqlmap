#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'

class Page(object):
    def __init__(self, url, html):
        self._url = url
        self._source = html

    @property
    def url(self):
        return self._url

    @property
    def source_page(self):
        return self._source
