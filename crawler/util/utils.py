__author__ = 'CwT'

import os

def execute(cmd):  # is used
    try:
        lines = os.popen(cmd).read().split('\n')
        for line in lines:
            if len(line.strip()) > 0:
                return True
    except:
        return False
    return False
