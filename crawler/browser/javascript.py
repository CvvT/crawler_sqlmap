#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'

# document.body.innerHTML += '<form id="dynForm" action="http://example.com/" method="post">
# <input type="hidden" name="q" value="a"></form>';
# document.getElementById("dynForm").submit();


POST_JS = '<form id=\\"dynamicform\\" action=\\"%s\\" method=\\"post\\">%s</form>'
INPUT_JS = '<input type=\\"hidden\\" name=\\"%s\\" value=%s>'
EXECUTE_JS = 'document.body.innerHTML = "%s"; document.getElementById("dynamicform").submit();'

def post_js(url, data):
    input = ""
    for key, value in data.items():
        if isinstance(value, int):
            input += INPUT_JS % (key, str(value))
        else:
            input += INPUT_JS % (key, "\\\"%s\\\"" % value)
    form = POST_JS % (url, input)
    return EXECUTE_JS % form
