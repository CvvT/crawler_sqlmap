#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import urllib.parse as urlparse
import json
import os
import time
import traceback

from urllib.parse import urlencode
from bs4 import BeautifulSoup
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver import FirefoxProfile
from selenium.common.exceptions import WebDriverException

from .browser.headlessBrowser import HeadlessBrowser
from .util.scheduler import Scheduler
from .util.urleliminate import UrlEliminator
from .util.findPageForm import findPageForm
from .proxy.proxy import ProxyDaemon
from .setting import Setting
from .autosql import Autosql
from .util.lookup import lookup, initialize
from .util.utils import execute

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
    def __init__(self, base_dir, sqlmap_ip, sqlmap_port, target=None, data=None, setting=None):
        self.base_dir = base_dir
        self.setting = setting if setting else Setting(True)
        self.entry = target if target else self.setting.url
        if not self.entry:
            raise ValueError("Empty target")
        self.setting.display()

        # initialize http/https proxy and start browser
        self.proxy = self.initProxy()
        self.initBrowser(self.proxy)

        # task scheduler
        self.scheduler = Scheduler()
        self.scheduler.add_task(self.entry, 0, data)

        # eliminate duplicate url
        self.eliminator = UrlEliminator(entry=self.entry, setting=self.setting)    # mark initial page/url visited

        # initialize sqlmap manager
        self.sqlScanner = Autosql(sqlmap_ip, sqlmap_port)

    def run(self):
        """启动扫描任务

        初始化完成后，调用本函数启动扫描
        :return:
        """
        while True:
            try:
                self.scheduler.run(self.browser, self.sqlScanner, self.setting)
                break
            except WebDriverException:
                if execute("ps | awk '{print $4}' | grep firefox"):  # still alive or not
                    self.scheduler.flush()
                    logger.error(traceback.format_exc())
                    break
                # restart headless browser
                self.initBrowser(self.proxy)
            except:
                logger.error(traceback.format_exc())
                self.scheduler.flush()
                break

    def report(self):
        self.scheduler.wait()
        self.sqlScanner.wait_task(interval=10)
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
        initialize(self.base_dir)
        self.scheduler.wait()
        self.sqlScanner.wait_task(interval=10)
        cont = {task: data for task, data in self.sqlScanner.data_tasks().items()
                if data and len(data) >= 2}
        simple = list()
        for task, data in cont.items():
            val = dict()
            for each in data:
                typ = each["type"]
                if typ == 0:
                    val["x_url"] = task
                    for string in ["url", "query", "data"]:
                        val[string] = each["value"][string] if each["value"][string] else ""
                elif typ == 1:
                    payload = list()
                    for vector in each["value"]:
                        for no, content in vector["data"].items():
                            payload.append({
                                "description": content["title"],
                                "vector": content["vector"],
                                "payload": content["payload"],
                                "method": vector['place']
                            })
                    for each_payload in payload:
                        lookup(each_payload, translate=True)
                        each_payload['vid'] = ''
                        each_payload['reference'] = dict()
                        if not isinstance(each_payload['vector'], str):
                            each_payload['vector'] = json.dumps(each_payload['vector'])
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

    def initBrowser(self, proxy):
        profile = self.setProxy(proxy)
        capabilities = DesiredCapabilities.FIREFOX.copy()
        capabilities['acceptSslCerts'] = True
        capabilities['acceptInsecureCerts'] = True

        # initialize headless browser
        try:
            self.browser = HeadlessBrowser(firefox_profile=profile, capabilities=capabilities)
        except WebDriverException:
            self.browser = HeadlessBrowser(firefox_profile=profile)
        # catch signal whenever a page is loaded
        self.browser.onfinish.connect(self.parse_page)
        self.browser.state_experiment(self.setting.experiment)

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
        if "mozilla" in _url:   # well, we're using firefox...
            return
        _data = dict()
        _depth = self.browser.current_depth
        if flow.request.method == "POST":
            for k in flow.request.query:
                _data[k] = flow.request.query[k]
            self.add_task(_url, _depth+1, data=_data)
        else:
            self.add_task(_url, _depth+1)

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
                    self.add_task(url, page.depth+1)
        except Exception as e:
            logger.error("[parse page error]")
            logger.error(traceback.format_exc())
        finally:
            # logger.debug("seaching for forms...")
            for url, method, data in findPageForm(page.source_page, page.url):
                logger.debug("find one form in %s" % url)
                if method.upper() == "GET":
                    url = "%s?%s" % (url, urlencode(data))
                    self.add_task(url, page.depth+1)
                elif method.upper() == "POST":
                    self.add_task(url, page.depth+1,
                                  json.loads(data) if isinstance(data, str) else data)
