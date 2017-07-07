# -*- coding: utf-8 -*-
__author__ = 'CwT'

import os

from xml.etree.ElementTree import parse

Corpus = dict()
XML_PATH = "sqlmap/xml/payloads"

RISK_LEVEL = {"1": "Low", "2": "Medium", "3": "High"}
RISK_LEVEL_CHINESE = {"1": u"\u4f4e", "2": u"\u4e2d", "3": u"\u9ad8"}
FAMILY_TYPE = {
    "1": "Boolean-based blind SQL injection",
    "2": "Error-based queries SQL injection",
    "3": "Inline queries SQL injection",
    "4": "Stacked queries SQL injection",
    "5": "Time-based blind SQL injection",
    "6": "UNION query SQL injection",
}
FAMILY_TYPE_CHINESE = {
    "1": u"\u0073\u0071\u006c\u76f2\u6ce8\u6f0f\u6d1e",  # "sql盲注漏洞",
    "2": u"\u0073\u0071\u006c\u9519\u8bef\u7c7b\u578b\u6ce8\u5165\u6f0f\u6d1e",  # "sql错误类型注入漏洞",
    "3": u"\u0073\u0071\u006c\u5185\u8054\u6ce8\u5165\u6f0f\u6d1e",  # sql内联注入漏洞",
    "4": u"\u0073\u0071\u006c\u591a\u8bed\u53e5\u67e5\u8be2\u6ce8\u5165\u6f0f\u6d1e",  # sql多语句查询注入漏洞",
    "5": u"\u0073\u0071\u006c\u65f6\u95f4\u6ce8\u5165\u6f0f\u6d1e",  # "sql时间注入漏洞",
    "6": u"\u0073\u0071\u006c\u8054\u5408\u67e5\u8be2\u6ce8\u5165\u6f0f\u6d1e",  # "sql联合查询注入漏洞",
}


def initialize(base_dir):
    payload_path = os.path.join(base_dir, XML_PATH)
    for path in os.listdir(payload_path):
        if not path.endswith('.xml'):
            continue
        with open(os.path.join(payload_path, path), 'r') as f:
            doc = parse(f)
            for item in doc.iterfind('test'):
                risk = item.findtext('risk')
                typ = item.findtext('stype')
                title = item.findtext('title')
                Corpus[title] = (risk, typ)


def jaccard_score(s1, s2):
    return len([i for i in s1 if i in s2])


def find_item(title):
    if title in Corpus:
        return title
    terms = title.split(' ')
    scores = dict()
    for each in Corpus.keys():
        scores[each] = jaccard_score(terms, each.split(' '))
    ret = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ret[0][0]


def lookup(item, translate=False):
    risk_dict = RISK_LEVEL_CHINESE if translate else RISK_LEVEL
    family_dict = FAMILY_TYPE_CHINESE if translate else FAMILY_TYPE
    ret = find_item(item['description'])
    if not ret:
        item['risk_level'] = 'High'
        item['name'] = 'unknown'
    else:
        risk_level, desc = Corpus[ret]
        item['risk_level'] = risk_dict[risk_level]
        item['name'] = family_dict[desc]
    item['category'] = 'sql injection' if not translate else u"\u0073\u0071\u006c\u6ce8\u5165\u6f0f\u6d1e"


if __name__ == '__main__':
    initialize("/home/cwt/crawler_sqlmap")
    item = {
        "vector": "AND [INFERENCE]",
        "payload": "msg=abc&id=1 AND 9130=9130",
        "title": "MySQL UNION query (NULL) - 1 to 20 columns",
        "method": "post"
    }
    lookup(item, True)
    for key, val in item.items():
        print(key)
        print(val)
