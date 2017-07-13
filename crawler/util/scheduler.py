#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'
from queue import Queue, Empty
import logging
import json

from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Scheduler(object):
    def __init__(self):
        self.FIFOqueue = Queue()

    def wait(self):
        logger.debug("start to exit, remaining tasks %d" % self.FIFOqueue.qsize())
        self.FIFOqueue.join()

    def add_task(self, target, depth, data=None):
        # print("Add one target to scheduler", target)
        self.FIFOqueue.put((target, data, depth))

    def get_task(self, block=False):
        return self.FIFOqueue.get(block=block)

    def flush(self):
        while not self.FIFOqueue.empty():
            self.get_task()
            self.FIFOqueue.task_done()

    def run(self, browser, scanner, setting):
        try:
            while True:
                # print("Get one", self.FIFOqueue.qsize())
                target, data, depth = self.get_task()
                # print("Target: ", target)
                options = {
                    "url": target,
                    "batch": True,
                    "level": setting.level,
                    "threads": setting.threads,
                    "timeout": setting.timeout
                }

                if data:
                    post_data = '&'.join(["%s=%s" % (k, v) for k, v in data.items()])
                    options["data"] = post_data

                if setting.test:
                    logger.debug("options: %s" % json.dumps(options))

                if not setting.test:
                    scanner.add_and_start(**options)

                try:
                    if depth >= setting.depth != -1:
                        continue
                    if data:
                        browser.post(target, data, depth)
                    else:
                        browser.request(target, depth)
                except TimeoutException:
                    pass
                except WebDriverException:
                    logger.error("firefox shutdown")
                    self.add_task(target, depth, data=data)  # add back and see if we can re-try
                    raise
                finally:
                    self.FIFOqueue.task_done()
        except Empty:
            logger.debug("Empty queue, ready to quit")
        except:
            raise


