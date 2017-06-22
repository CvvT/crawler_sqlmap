#! /usr/bin/env python
# -*- coding: utf-8 -*-

def after(caller_name, *caller_args, **caller_kwargs):
    '''
    Connect two functions of the same class to execute in order as the function name means
    :param caller_name: Given the name of the function which should be called afterwards
    :param caller_args:
    :param caller_kwargs:
    :return:
    '''
    def signal(callee):
        def wrapper(*args, **kwargs):
            callee(*args, **kwargs)
            caller = getattr(args[0], caller_name, None)
            if not caller:
                raise AttributeError("The class doesn't have this func: %s" % caller_name)
            caller(*caller_args, **caller_kwargs)
        return wrapper
    return signal

def before(caller_name, *caller_args, **caller_kwargs):
    '''
    The same as `after` except the execution order of the two functions
    :param caller_name:
    :param caller_args:
    :param caller_kwargs:
    :return:
    '''
    def signal(callee):
        def wrapper(*args, **kwargs):
            caller = getattr(args[0], caller_name, None)
            if not caller:
                raise AttributeError("The class doesn't have this func: %s" % caller_name)
            caller(*caller_args, **caller_kwargs)
            callee(*args, **kwargs)
        return wrapper
    return signal