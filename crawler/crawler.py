#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import urllib.parse as urlparse
import json
import os
import time

from urllib.parse import urlencode
from bs4 import BeautifulSoup
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver import FirefoxProfile

from .browser.headlessBrowser import HeadlessBrowser
from .util.scheduler import Scheduler
from .util.urleliminate import UrlEliminator
from .util.findPageForm import findPageForm
from .proxy.proxy import ProxyDaemon
from .setting import Setting
from .util import Global
from .autosql import Autosql

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Crawler(object):
    """网页爬虫管理类，负责调度各项任务。

    此类主要包含几个模块：
        1. browser: 浏览器模块
        2. scheduler: 任务调度模块
        3. elimiator: url去重模块
        4. proxy: 代理模块
        5. salScanner: sqlmap任务调度模块
    """
    def __init__(self, base_dir, target=None, data=None, setting=Setting()):
        self.base_dir = base_dir
        self.entry = setting.url if setting.url else target
        if not self.entry:
            raise ValueError("Empty target")
        self.setting = setting
        self.setting.display()

        # initial http/https proxy
        self.proxy = self.initProxy()
        profile = self.setProxy(self.proxy)
        capabilities = DesiredCapabilities.FIREFOX.copy()
        capabilities['acceptSslCerts'] = True
        capabilities['acceptInsecureCerts'] = True

        # task scheduler
        self.scheduler = Scheduler()
        self.scheduler.add_task(self.entry, Global.CURRENT_DEPTH, data)

        # eliminate duplicate url
        self.eliminator = UrlEliminator(entry=target, setting=self.setting)    # mark initial page/url visited

        # initialize headless browser
        self.browser = HeadlessBrowser(firefox_profile=profile, capabilities=capabilities)
        # catch signal whenever a page is loaded
        self.browser.onfinish.connect(self.parse_page)

        # initialize sqlmap manager
        self.sqlScanner = Autosql(Global.SERVER_IP, Global.SERVER_PORT)

    def run(self):
        """启动扫描任务

        初始化完成后，调用本函数启动扫描
        :return:
        """
        self.scheduler.run(self.browser, self.sqlScanner, self.setting)

    def report(self):
        self.scheduler.wait()
        self.sqlScanner.wait_task(interval=20)
        timestrip = time.strftime("%Y-%m-%d", time.localtime())
        with open(os.path.join(self.setting.output, "report_%s.json" % timestrip), "w") as f:
            cont = {task: data for task, data in self.sqlScanner.data_tasks().items()
                    if data and len(data) > 0}
            f.write(json.dumps(cont))

    def raw_report(self):
        """返回sqlmap扫描结果

        :return: 返回值为三元组（ret, content, simple）
            ret: 执行结果, False为失败, True为成功
            content: sqlmap返回的完整报告，字典类型
            simple: 解析content抽取重要数据生成的报告，字典类型
        """
        self.scheduler.wait()
        self.sqlScanner.wait_task(interval=20)
        cont = {task: data for task, data in self.sqlScanner.data_tasks().items()
                if data and len(data) >= 2}
        simple = list()
        for task, data in cont.items():
            val = dict()
            for each in data:
                typ = each["type"]
                if typ == 0:
                    val["x_url"] = task
                    for str in ["url", "query", "data"]:
                        val[str] = each["value"][str] if each["value"][str] else ""
                elif typ == 1:
                    payload = list()
                    for vector in each["value"]:
                        for no, content in vector["data"].items():
                            payload.append({
                                "title": content["title"],
                                "vector": content["vector"],
                                "payload": content["payload"],
                                "method": vector['place']
                            })
                    val["vuls"] = payload
            simple.append(val)
        return cont, {"result": simple}

    def close(self):
        """关闭所有相关组件

        扫描完成后，关闭浏览器、sqlmap以及proxy
        :return:
        """
        self.browser.close()
        # delete all tasks
        self.sqlScanner.flush_tasks()
        # make sure close proxy at last
        self.proxy.stop()

    def initProxy(self):
        proxy = ProxyDaemon(cadir=os.path.join(self.base_dir, "ssl/"))
        proxy.daemon = True
        proxy.proxy.requested.connect(self.handle_request)
        proxy.start()
        return proxy

    def setProxy(self, proxy):
        profile = FirefoxProfile()
        profile.accept_untrusted_certs = True
        profile.assume_untrusted_cert_issuer = True
        prefix = "network.proxy."
        profile.set_preference("%stype" % prefix, 1)
        for type in ["http", "ssl", "ftp", "socks"]:
            profile.set_preference("%s%s" % (prefix, type), proxy.getHost())
            profile.set_preference("%s%s_port" % (prefix, type), int(proxy.getPort()))
        return profile

    def handle_request(self, flow):
        # logger.debug("*"*16)
        # logger.debug(flow.request.pretty_host)
        # logger.debug("proxy: %s" % flow.request.url)
        # logger.debug(flow.request.method)
        _url = str(flow.request.url)
        if "mozilla" in _url:
            return
        _data = dict()
        if flow.request.method == "POST":
            for k in flow.request.query:
                _data[k] = flow.request.query[k]
            self.add_task(_url, Global.CURRENT_DEPTH+1, data=_data)
        else:
            self.add_task(_url, Global.CURRENT_DEPTH+1)

    def add_task(self, url, depth, data=None):
        if self.eliminator.visit(url):
            self.scheduler.add_task(url, depth, data=data)

    def parse_page(self, page):
        """
        Parse page
        :param page: see browser.page.Page class
        :return:
        """
        if not page:
            logger.error("skip this page")
            return

        try:
            match = re.search(r"(?si)<html[^>]*>(.+)</html>", page.source_page)
            if match:
                content = "<html>%s</html>" % match.group(1)
            soup = BeautifulSoup(content, "html.parser")
            tags = soup('a')

            if not tags:
                tags = re.finditer(r'(?si)<a[^>]+href="(?P<href>[^>"]+)"', content)

            for tag in tags:
                href = tag.get("href") if hasattr(tag, "get") else tag.group("href")

                if href:
                    url = urlparse.urljoin(page.url, href)
                    self.add_task(url, Global.CURRENT_DEPTH+1)
        except Exception as e:
            logger.error("[parse page error]%s" % e.message)
            logger.error(type(e))
        finally:
            # logger.debug("seaching for forms...")
            for url, method, data in findPageForm(page.source_page, page.url):
                logger.debug("find one form %s" % url)
                if method.upper() == "GET":
                    url = "%s?%s" % (url, urlencode(data))
                    self.add_task(url, Global.CURRENT_DEPTH+1)
                elif method.upper() == "POST":
                    self.add_task(url, Global.CURRENT_DEPTH+1,
                                  json.loads(data) if isinstance(data, str) else data)
