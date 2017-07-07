#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'
import logging
import time
import subprocess
import sys
import os
import json
import traceback

from crawler.crawler import Crawler
from crawler.util import Global
from crawler.setting import Setting

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
HINT = 0


def check_port(port):  # is used
    lines = os.popen("netstat -at | awk '{print $4}' | grep %d" % port).read().split("\n")
    for line in lines:
        if len(line.strip()) > 0:
            return True
    return False


def get_available_port():
    global HINT
    while True:
        port = 21345 + HINT
        HINT += 1
        if not check_port(port):
            return port


def start_sqlmap():
    port = get_available_port()
    Global.SERVER_PORT = port
    sqlmap = subprocess.Popen(["python2", "sqlmapapi.py", "-s", "-p", str(Global.SERVER_PORT),
                               "-H", Global.SERVER_IP], cwd=os.path.join(BASE_DIR, "sqlmap"))
    while check_port(port):
        logger.debug("wait 5 seconds for sqlmap initialization")
        time.sleep(5)  # wait 5 seconds for sqlmap initialization
    return sqlmap


def crawler_sqlmap(entry_url, depth=-1, level=1, threads=2, timeout=30, checkhost=True):
    """启动sqlmap扫描的入口函数。

    :param entry_url: 扫描网站的入口地址
    :param depth: 网页爬虫爬取页面深度，－1则表示不设置深度，默认－1
    :param level: sqlmap扫描测试等级：1-5（默认为1），等级越高使用的测试样例越多，结果越精确，时间也越长
    :param threads: sqlmap多线程扫描设置（默认为2）
    :param timeout: sqlmap扫描超时时间（默认30s）
    :param checkhost: 检查爬取链接是否属于同一域
    :return: 返回值为四元组（ret, url, simple, content）
            ret: 执行结果, False为失败, True为成功
            url: 扫描目标地址
            simple: 解析content抽取重要数据生成的报告，字典类型
            content: sqlmap返回的完整报告，字典类型
            若执行结果为False，那么把扫描错误信息存在扫描关键结果（simple）这个位置
    """
    settings = Setting(handle=False)
    settings.depth = depth
    settings.nocheckhost = not checkhost
    settings.level = level
    settings.threads = threads
    settings.timeout = timeout

    sqlmap, crawler = None, None
    try:
        sqlmap = start_sqlmap()
        # crawler的创建必须在sqlmap启动之后, 才能正确获取sqlmap的端口号
        crawler = Crawler(BASE_DIR, entry_url, setting=settings)
        crawler.run()
        cont, simple = crawler.raw_report()
        return True, entry_url, simple, cont
    except:
        traceback.print_exc()
        return False, entry_url, traceback.format_exc(), {}
    finally:
        if crawler: crawler.close()
        if sqlmap: sqlmap.terminate()

if __name__ == '__main__':
    # ret, url, simp, cont = crawler_sqlmap("http://testphp.vulnweb.com/")
    # print(json.dumps(simp))
    sqlmap, crawler = None, None
    try:
        sqlmap = start_sqlmap()
        crawler = Crawler(BASE_DIR, "http://testphp.vulnweb.com/")
        crawler.run()
        crawler.report()
    finally:
        # print("close")
        crawler.eliminator.display()
        if crawler:
            crawler.close()
        if sqlmap: sqlmap.terminate()
        while True:
            sys.exit(1)
