#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import json
import traceback

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoAlertPresentException, WebDriverException

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

        self._experiment = False
        self._depth = -1
        # signal
        self.onfinish = Finish()

        super(HeadlessBrowser, self).__init__(**kwargs)

    @property
    def current_depth(self):
        return self._depth

    def close(self):
        logger.debug("start to quit browser")
        try:
            self.quit()
        except WebDriverException:
            logger.error("firefox shutdown earlier")
        self.display.stop()

    def state_experiment(self, value):
        self._experiment = value

    @after("finished")
    def request(self, url, depth):
        """Get request

        :param url:
        :param depth:
        :return:
        """
        logger.debug("[*]Processing %s" % url)
        self._depth = depth
        self.get(url)    # synchronous api

    @after("finished")
    def post(self, url, data, depth):
        """Post request

        :param url:
        :param data:
        :param depth:
        :return:
        """
        logger.debug("[*]Processing %s with %s" % (url, json.dumps(data)))
        self._depth = depth
        self.execute_script(post_js(url, data))  # synchronous api???

    def click_buttons(self):
        """

        consider the consequence of clicking buttons:
        1. redirect: well, redirecting usually occurs with tag 'a' rather than 'button' or 'input', so I
                    ignore this situation right now. Maybe I shouldn't?
        2. alert: handler alert well
        :return:
        """
        btns = self.find_elements_by_tag_name("button")
        for btn in btns:
            try:
                logger.debug("find a button and click on it")
                btn.click()
                self.switch_to.alert.accept()
            except NoAlertPresentException:
                pass
            except:
                traceback.print_exc()
        btns = self.find_elements_by_xpath('//input[@type="button"]')
        # btns = self.find_elements_by_xpath('//input[@onclick]')
        for btn in btns:
            try:
                btn.click()
                self.switch_to.alert.accept()
            except NoAlertPresentException:
                pass
            except:
                traceback.print_exc()
            # it seems like we can declare that the button isn't inside a form
            # make sure it isn't inside a form
            # try:
            #     form = btn.find_element_by_xpath('./ancestor::form')
            # except NoSuchElementException:
            #     try:
            #         btn.click()
            #     except:
            #         traceback.print_exc()
            # else:
            #     logger.debug("it is inside a form")

    def finished(self):
        try:
            # make sure js has executed
            wait = WebDriverWait(self, 10)
            wait.until(jQuery_load())
            wait.until(jScript_load())
            # deal with buttons which may change the content
            if self._experiment:
                _url = self.current_url
                self.click_buttons()
                if _url != self.current_url:
                    logger.error("[error]page direct from %s to %s" % (_url, self.current_url))
            page = Page(self.current_url, self.page_source, self._depth)
            self.onfinish(page)
        except Exception as e:    # TimeoutException:
            logger.error("error!!")
            logger.error(e)
            traceback.print_exc()
            self.onfinish(None)

    # support with notation 'with'
    def __enter__(self):
        # All work should be done while initializing
        pass

    def __exit__(self, type, value, trace):
        self.close()
