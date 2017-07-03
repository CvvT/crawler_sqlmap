#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'

class Page(object):
    def __init__(self, url, html, depth):
        self._url = url
        self._source = html
        self._depth = depth

    @property
    def url(self):
        return self._url

    @property
    def source_page(self):
        return self._source

    @property
    def depth(self):
        return self._depth
