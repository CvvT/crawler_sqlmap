#! /usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import json
import time
import logging
import traceback

logger = logging.getLogger("autosql")
logger.setLevel(logging.DEBUG)

class Autosql(object):
    """sqlmap任务管理模块

    通过Restful API与sqlmap server通信，创建、开始、停止任务，获取扫描结果
    """
    def __init__(self, addr="127.0.0.1", port=8775):
        self._server = addr
        self._port = port
        self._tasks = []
        self._nameMap = {}

    def server_addr(self):
        return "http://%s:%d" % (self._server, self._port)
    
    def add_task(self):
        url = "%s/task/new" % self.server_addr()
        try:
            ret = requests.get(url)
            jsonobj = json.loads(ret.text)
            if not jsonobj["success"]:
                return None
            taskId = jsonobj["taskid"]
            logger.debug("[add task] add task %s" % taskId)
            self._tasks.append(taskId)
        except:
            traceback.print_exc()
            return None
        return taskId

    def delete_task(self, taskid):
        url = "%s/task/%s/delete" % (self.server_addr(), taskid)
        logger.debug("[delete task] delete task %s" % taskid)
        try:
            ret = requests.get(url)
            jsonobj = json.loads(ret.text)
            index = self._tasks.index(taskid)
            del self._tasks[index]
            return jsonobj["success"]
        except:
            return False

    def stop_task(self, taskid):
        url = "%s/scan/%s/stop" % (self.server_addr(), taskid)
        logger.debug("[stop task] stop task %s" % taskid)
        try:
            ret = requests.get(url)
            jsonobj = json.loads(ret.text)
            return jsonobj["success"]
        except:
            return False

    def start_task(self, taskid, **kwargs):
        """启动一个扫描任务

        :param taskid: 任务id
        :param kwargs: 任务参数配置，其中包括
                    options {
                        crawlDepth=3
                        url="http://xxxx"
                        forms=True
                        batch=True
                        cookie="a=b;c=d"
                    }
        :return: True or False
        """
        self._nameMap[taskid] = kwargs["url"]

        url = "%s/scan/%s/start" % (self.server_addr(), taskid)
        logger.debug("[start task] start task %s" % taskid)
        options = dict()
        for k, v in kwargs.items():
            options[k] = v
            
        try:
            headers = {"Content-Type": "application/json"}
            ret = requests.post(url, data=json.dumps(options), headers=headers)
            jsonobj = json.loads(ret.text)
            if jsonobj["success"]:
                return True
        except:
            traceback.print_exc()
            return False
        return False

    def status_task(self, taskid):
        """返回指定任务状态

        :param taskid: 任务id
        :return: [running|not running|terminated]
        """
        url = "%s/scan/%s/status" % (self.server_addr(), taskid)
        try:
            ret = requests.get(url)
            jsonobj = json.loads(ret.text)
            if jsonobj["success"]:
                return jsonobj["status"]
        except:
            traceback.print_exc()
            return None

    def add_and_start(self, **kwargs):
        taskid = self.add_task()
        # logger.debug("[add and start] get taskid %s" % taskid)
        if taskid:
            # for k, v in kwargs.items():
            #     logger.debug("[*]%s: %s" % (k, v))
            if not self.start_task(taskid, **kwargs):
                # ignore return value??
                logger.debug("starting task %s failed" % taskid)
                self.delete_task(taskid)
                return False
            return True
        else:
            logger.error("[add task error]!!!!!")
        return False

    def wait_task(self, taskid=-1, timeout=-1, stop=False, interval=10):
        """
        wait until the specific task finishs or time out if given time>0. Start it if it's not running at all.
        Wait all tasks finish if given taskid=-1
        stop tasks if parameter stop is set true
        """
        start = time.time()
        if taskid != -1:
            while True:
                status = self.status_task(taskid)
                if not status:
                    raise ValueError("Invalid taskid %s" % taskid)
                if status == "not running":
                    self.start_task(taskid)
                elif status == "terminated":
                    return
                time.sleep(interval)
                if 0 < timeout < time.time() - start:
                    if stop: # ignore return value?
                        self.stop_task(taskid)
                    return
        else:
            logger.debug("%d tasks remained" % len(self._tasks))
            index = 0
            while True:
                for i in range(index, len(self._tasks)):
                    task = self._tasks[i]
                # for task in self._tasks[index:]:
                    status = self.status_task(task)
                    logger.debug("[wait task] status of task %s: %s" % (task, status))
                    if not status:
                        raise ValueError("Invalid taskid %s" % task)
                    if status == "not running":
                        self.start_task(task)
                        break
                    elif status == "running":
                        break
                    index += 1
                else:
                    return
                time.sleep(interval)
                if 0 < timeout < time.time() - start:
                    if stop:
                        for task in self._tasks:
                            status = self.start_task(task)
                            if status and status == "running":
                                self.stop_task(task)
                    return
        
    def flush_tasks(self):
        '''
        kill all remaining tasks
        '''
        for task in self._tasks:
            self.delete_task(task)
        
    def data_task(self, taskid):
        url = "%s/scan/%s/data" % (self.server_addr(), taskid)
        logger.debug("[data task] get data from %s" % taskid)
        try:
            ret = requests.get(url)
            jsonobj = json.loads(ret.text)
            if jsonobj["success"]:
                return jsonobj["data"]
            else:
                logger.error("Retrieve data error: %s" % jsonobj["error"])
        except Exception as e:
            logger.error(e)
        return None

    def data_tasks(self):
        # return {self._nameMap[k]: self.data_task(k) for k in self._tasks}
        ret = dict()
        for task in self._tasks:
            data = self.data_task(task)
            ret[self._nameMap[task]] = data
        return ret

    def scan_log(self, taskid):
        url = "%s/scan/%s/log" % (self.server_addr(), taskid)
        logger.debug("[scan log] get log from %s" % taskid)
        try:
            ret = requests.get(url)
            jsonobj = json.loads(ret.text)
            if jsonobj["success"]:
                return jsonobj["log"]
        except:
            pass
        return []
    
# if __name__ == '__main__':
#     manager = Autosql()
#     try:
#         manager.add_and_start(url="http://localhost/dvwa/vulnerabilities/sqli/index.php",
#                               crawlDepth=3, forms=True, batch=True,
#                               cookie="security=low;PHPSESSID=feuanil767rl7u5d4id9fqgt20")
#         manager.wait_task(interval=20)
#         # display results
#         for task, data in manager.data_tasks().items():
#             logger.debug("%s:" % task)
#             logger.debug("\t%s" % str(data))
#             if len(data) > 0:
#                 logger.info("find sql injection")
#     finally:
#         manager.flush_tasks()
