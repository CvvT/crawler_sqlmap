#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'

import logging

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-d", "--depth", dest="depth", action="store", default=-1, type="int",
                  help="the distance from a starting location")
parser.add_option("--nocheckhost", dest="nocheckhost", action="store_true", default=False,
                  help="don't check host for crawler")
parser.add_option("--level", dest="level", action="store", default=1, type="int",
                  help="sqlmap scan level(from 1-5, default 1)")
parser.add_option("--timeout", dest="timeout", action="store", default=30, type="int",
                  help="sqlmap timeout for each task")
parser.add_option("-u", "--url", dest="url", action="store", default=None,
                  help="target url")
parser.add_option("--test", dest="test", action="store_true", default=False,
                  help="developer used only")
parser.add_option("--threads", dest="threads", action="store", default=1, type="int",
                  help="Max number of concurrent HTTP(s) requests (default 1)")
parser.add_option("-o", "--output", dest="output", action="store", default=".",
                  help="directory for report file")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

Default = {
    "depth": -1,
    "nocheckhost": False,
    "level": 1,
    "url": None,
    "threads": 1,
    "timeout": 30,
    "output": ".",
    "test": False
}

class Setting(object):
    def __init__(self, handle=False):
        self.__dict__.update(Default)

        if handle:
            options, argv = parser.parse_args()

            setattr(self, "url", options.url)
            setattr(self, "threads", options.threads)
            setattr(self, "timeout", options.timeout)
            setattr(self, "output", options.output)
            setattr(self, "depth", options.depth)
            setattr(self, "level", options.level)

            if options.nocheckhost: setattr(self, "nocheckhost", True)
            if options.test: setattr(self, "test", True)

    def __setattr__(self, key, value):
        self.__dict__[key] = value

    def __getattr__(self, item):
        return self.__dict__[item]

    def display(self):
        for k, v in self.__dict__.items():
            logger.debug("%s: %s" % (k, v))
