#! /usr/bin/env python
# -*- coding: utf-8 -*-

class Signal(object):
    def __init__(self):
        self.func = []

    def connect(self, func):
        self.func.append(func)

    def __call__(self, *args, **kwargs):
        for fun in self.func:
            fun(*args, **kwargs)


class Finish(Signal):
    def __init__(self):
        super(Finish, self).__init__()

class Request(Signal):
    def __init__(self):
        super(Request, self).__init__()

class Response(Signal):
    def __init__(self):
        super(Response, self).__init__()
