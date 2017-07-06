#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'

import urllib.parse as urlparse
import logging

IGNORED_EXTENSIONS = [
    # images
    'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
    'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg', 'ico',

    # audio
    'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

    # video
    '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
    'm4a',

    # other
    'css', 'pdf', 'doc', 'exe', 'bin', 'rss', 'zip', 'rar', 'js', 'xml',
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class UrlEliminator(object):
    """URL去重模块

    去除无需扫描或者重复的页面：
        1. 后缀为jpg等图片、视频页面
        2. 通过正则匹配去除重复页面
    """
    def __init__(self, entry=None, setting=None):
        self.visited = set()
        self.setting = setting
        if entry:
            self.entry = entry
            self.visited.add(entry)

    def visit(self, url):
        _url = self._urlRegexize(url)
        # logger.debug("[+]Regexized url %s-->%s" % (url, _url))
        if len(self.visited) == 0:
            self.entry = url
            self.visited.add(_url)
            return True

        if self.setting and not self.setting.nocheckhost and \
                not self._checkSameHost(self.entry, url):
            # logger.debug("It's not the same host %s" % url)
            return False

        if any(_url.endswith(".%s" % each) for each in IGNORED_EXTENSIONS):
            # note: we don't need to worry too much if the url ended with ignored extensions yet turn out to be
            # a normal page, since by here we have format the origin url into a more concise one
            return False
        if _url in self.visited:
            return False
        self.visited.add(_url)
        return True

    def _checkSameHost(self, *urls):
        if not urls:
            return None
        elif len(urls) == 1:
            return True
        else:
            return all(urlparse.urlparse(url or "").netloc.split(':')[0] ==
                       urlparse.urlparse(urls[0] or "").netloc.split(':')[0] for url in urls[1:])

    def _urlRegexize(self, url):
        # scheme://netloc/path;parameters?query#fragment
        # http://video.sina.com.cn/ent/s/h/2010-01-10/163961994.html?a=1&b=10
        # --> http://video.sina.com.cn/ent/s/h/d+-d+-d+/d+.html?a=&b=
        comp = urlparse.urlparse(url)
        path = comp.path
        i, start = 0, -1
        result = ''
        while i < len(path):
            if '0' <= path[i] <= '9':
                start = i if start == -1 else start
            elif start != -1:
                result += "\d+"
                start = -1
                continue
            else:
                result += path[i]
            i += 1
        if start != -1:
            result += "\d+"
        path = result

        query = ''
        for key in urlparse.parse_qs(comp.query).keys():
            if query != '': query += '&'
            query += (key+'=')
        # TODO: exclude params????
        return urlparse.urlunparse((comp.scheme, comp.netloc, path, comp.params, query, ""))

    def display(self):
        for url in self.visited:
            logger.debug(url)

# if __name__ == '__main__':
#     eliminator = UrlEliminator()
#     print(eliminator._urlRegexize("http://video.sina.com.cn/ent/s/h/2010-01-10/163961994.php?a=1&b=10"))
