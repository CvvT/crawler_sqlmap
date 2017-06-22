#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'
import logging
import os
import threading
import sys

from mitmproxy import master, controller, options
from mitmproxy.proxy import ProxyServer, ProxyConfig
from mitmproxy.exceptions import ServerException

from ..browser.signal import Request, Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HINT = 0

class Proxy(master.Master):
    def __init__(self, opts, server):
        super(Proxy, self).__init__(opts, server)
        self.requested = Request()
        self.responsed = Response()

    def run(self):
        try:
            logger.debug("start proxy")
            master.Master.run(self)
        except:
            pass
        finally:
            self.shutdown()
            logger.debug("stopping proxy server")

    @controller.handler
    def request(self, f):
        self.requested(f)

    @controller.handler
    def response(self, f):
        self.responsed(f)

    @controller.handler
    def error(self, f):
        logger.debug("proxy error:")
        logger.debug(f)

    # @controller.handler
    # def log(self, l):
    #     logger.debug("proxy log: %s" % l.msg)

class ProxyDaemon(threading.Thread):
    def __init__(self, port=12345, mode="regular", cadir="ssl/"):
        super(ProxyDaemon, self).__init__()

        if not os.path.exists(cadir):
            logger.error("%s does not exist" % cadir)
            raise ValueError("%s does not exist" % cadir)

        global HINT
        while True:
            try:
                opts = options.Options(
                    listen_port=port + HINT,
                    mode=mode,
                    cadir=cadir
                )

                config = ProxyConfig(opts)
                server = ProxyServer(config)
                self.port = port+HINT
                self.mproxy = Proxy(opts, server)
                break
            except ServerException:
                pass
            finally:
                HINT += 1

    @property
    def proxy(self):
        return self.mproxy

    def getProxy(self):
        return "%s:%d" % ("127.0.0.1", self.port)

    def getHost(self):
        return "127.0.0.1"

    def getPort(self):
        return self.port

    def run(self):
        self.mproxy.run()

    def stop(self):
        self.mproxy.shutdown()

