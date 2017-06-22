#! /usr/bin/env python
# -*- coding: utf-8 -*-

class jQuery_load(object):
    def __init__(self):
        pass

    def __call__(self, driver):
        try:
            ret = driver.execute_script("return jQuery.active")
            return int(ret) == 0
        except:
            return True

class jScript_load(object):
    def __init__(self):
        pass

    def __call__(self, driver):
        try:
            ret = driver.execute_script("return document.readyState")
            return str(ret) == "complete"
        except:
            return False
