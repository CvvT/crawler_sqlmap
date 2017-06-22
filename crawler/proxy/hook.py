#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def handleRequest(flow):
    logger.debug("*"*16)
    logger.debug(flow.request.pretty_host)
    logger.debug(flow.request.url)
    logger.debug(flow.request.method)
    logger.debug(str(flow.request.query))

def handleResponse(flow):
    pass
