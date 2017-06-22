#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json
import traceback

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from .decorator import after
from .signal import Finish
from .condition import jQuery_load, jScript_load
from .page import Page
from .javascript import post_js

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO: handle alert, confirm, prompt
class HeadlessBrowser(webdriver.Firefox):
    """无界面浏览器

    firefox+geckodriver+xvfb+pyvirtualdisplay实现无界面浏览页面
    """
    def __init__(self, **kwargs):
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        # signal
        self.onfinish = Finish()

        super(HeadlessBrowser, self).__init__(**kwargs)

    def close(self):
        logger.debug("start to quit browser")
        self.quit()
        self.display.stop()

    @after("finished")
    def get(self, url):
        logger.debug("[*]Processing %s" % url)
        super(HeadlessBrowser, self).get(url)    # synchronous api

    @after("finished")
    def post(self, url, data):
        logger.debug("[*]Processing %s with %s" % (url, json.dumps(data)))
        self.execute_script(post_js(url, data))  # synchronous api???

    def finished(self):
        try:
            # make sure js has executed
            wait = WebDriverWait(self, 10)
            wait.until(jQuery_load())
            wait.until(jScript_load())
            page = Page(self.current_url, self.page_source)
            self.onfinish(page)
        except Exception as e:    # TimeoutException:
            logger.error("error!!")
            logger.error(e)
            traceback.print_exc()
            self.onfinish(None)

    # support with notation
    def __enter__(self):
        # All work should be done while initializing
        pass

    def __exit__(self, type, value, trace):
        self.close()
