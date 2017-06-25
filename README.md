# Introduction

It's quite self-explanatory with its name: a cralwer with sqlmap to detect sql injection.

## Features

1. Currently it supports dealing with javascript with the help of selenuim.
2. Capture traffics with mitmproxy in order to discover ajax requests.
3. Able to extract infos from forms in page to construct Get/Post requests.

## To-DO:
Deal with interactive operations. For instance, a request can be generated and sent only after a user clicks on one button.

## Notice

It only works on Linux!!

# Usage：

## 通过命令行方式启动 (command line)
```
python crawler_sqlmap.py [options]

Options:
  -h, --help            使用帮助
  -d DEPTH, --depth=DEPTH
                        爬虫爬取深度，不设置则爬取所有链接
  --nocheckhost         不检查爬取链接是否属于同一域
  --level=LEVEL         sqlmap扫描测试等级：1-5（默认为1），等级越高使用的测试样例越多，结果越精确，时间也越长
  --timeout=TIMEOUT     sqlmap扫描超时时间（默认30s）
  -u URL, --url=URL     扫描入口
  --threads=THREADS     sqlmap多线程扫描设置（默认为1）
  -o OUTPUT, --output=OUTPUT
                        报告输出目录，默认为当前文件夹
```

  样例：
  ```
  python crawler_sqlmap.py -u "http://demo.aisec.cn/demo/aisec/" --threads=2
  ```

  输出结果保存在: OUTPUT/report_当前日期.json文件中

  输出结果为json格式，目前直接保存的是sqlmap返回的所有数据，其中比较重要的数据有：
  ```
  "value": {
                "url": "http://demo.aisec.cn:80/demo/aisec/js_link.php", //扫描目标url
                "query": "id=2&msg=abc", //get请求参数
                "data": null //post请求参数
            }

  "data": {
                "1": { //可能有多个注入方式
                    "comment": "",
                    "matchRatio": 0.916,
                    "trueCode": 200,
                    "title": "AND boolean-based blind - WHERE or HAVING clause", //sql注入方式
                    "templatePayload": null,
                    "vector": "AND [INFERENCE]",
                    "falseCode": 200,
                    "where": 1,
                    "payload": "id=2 AND 3375=3375&msg=abc" //sql注入内容
                }
           }
  ```

## 通过函数调用的方式启动 (function call)

```
def main(entry_url, depth=-1, level=1, threads=1, timeout=30, checkhost=True)
```

参数含义与命令行参数相同，除了checkhost与命令行的nocheckhost相反

样例：
```
from test import main
ret, url, simple, content = main("http://demo.aisec.cn/demo/aisec/", depth=1)
```
ret: 执行结果, False为失败, True为成功

simple: 解析content抽取重要数据生成的报告，字典类型

content: sqlmap返回的完整报告，字典类型

  完整输出样例：
  ````
  {
    "http://demo.aisec.cn/demo/aisec/js_link.php?id=2&msg=abc": [
        {
            "status": 1,
            "type": 0,
            "value": {
                "url": "http://demo.aisec.cn:80/demo/aisec/js_link.php",
                "query": "id=2&msg=abc",
                "data": null
            }
        },
        {
            "status": 1,
            "type": 1,
            "value": [
                {
                    "dbms": null,
                    "suffix": "",
                    "clause": [
                        1,
                        9
                    ],
                    "notes": [],
                    "ptype": 1,
                    "dbms_version": null,
                    "prefix": "",
                    "place": "GET",
                    "os": null,
                    "conf": {
                        "code": null,
                        "string": "has this record.",
                        "notString": null,
                        "titles": false,
                        "regexp": null,
                        "textOnly": false,
                        "optimize": false
                    },
                    "parameter": "id",
                    "data": {
                        "1": {
                            "comment": "",
                            "matchRatio": 0.916,
                            "trueCode": 200,
                            "title": "AND boolean-based blind - WHERE or HAVING clause",
                            "templatePayload": null,
                            "vector": "AND [INFERENCE]",
                            "falseCode": 200,
                            "where": 1,
                            "payload": "id=2 AND 3375=3375&msg=abc"
                        }
                    }
                }
            ]
        }
    ]
}
````

解析后生成的字典：
````
{
   “result”:[
	{
    		“x_url”: ”http://demo.aisec.cn/demo/aisec/post_link.php?aa=bb",
    		"url": "http://demo.aisec.cn:80/demo/aisec/post_link.php", //测试地址
    		"query”: ””,                                               //GET请求数据，如果是null设置成空字符（“”）
    		"data": "msg=abc&m' 'sg=abc&i' 'd=1&B1=提交&id=1&”,         //POST请求数据，如果是null设置成空字符（“”）
    		"vuls": [
 		        {
            		"vector": "AND [INFERENCE]",                                 //注入类型
            		"payload": "msg=abc&id=1 AND 9130=9130",                     //注入payload
            		"title": "AND boolean-based blind - WHERE or HAVING clause”, //注入方式
	    		    “method”:”post”						     //GET或者POST方式
         	    }
     		]
  	},
   ]
}
````

# 环境配置 (requirements)：

需要的软件包括：
1. mitmproxy: http://docs.mitmproxy.org/en/stable/install.html
````
sudo apt-get install python3-dev python3-pip libffi-dev libssl-dev
sudo pip3 install mitmproxy  # or pip3 install --user mitmproxy
````
2. firefox:
````
https://ftp.mozilla.org/pub/firefox/nightly/2017/03/2017-03-04-11-02-10-mozilla-central/firefox-54.0a1.en-US.linux-x86_64.tar.bz2
下载firefox放至/opt/firefox
ln -s /opt/firefox/firefox /usr/bin/firefox
````
3. xvfb:
````
sudo apt-get install xvfb
````
4. geckodriver:
````
https://github.com/mozilla/geckodriver/releases
下载完成后解压至/usr/bin或/usr/local/bin
注意：由于默认安装的selenium版本不是最新版，请下载版本<= 0.14.0
````
5. selenium:
````
pip3 install selenium
````
6. pyvirtualdisplay:
````
sudo pip3 install pyvirtualdisplay
````
7. beautifulsoup4:
````
pip3 install beautifulsoup4
````
8. requests:
````
pip3 install requests
````
9. python2, python3:
````
sqlmap必须运行在python2的环境下
````

10. sqlmap:
````
git submodule update --init --recursive
````
