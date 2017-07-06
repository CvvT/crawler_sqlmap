#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'CwT'
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def extract_form_fields(soup):
    """Turn a BeautifulSoup form in to a dict of fields and default values"""
    fields = {}
    for input in soup.find_all('input'):
        # ignore submit/image with no name attribute
        typ = input['type'].lower() if input.has_attr('type') else 'text'   # set default type for input element
        if typ in ('submit', 'image') and not input.has_attr('name'):
            continue

        # single element nome/value fields
        if typ in ('text', 'hidden', 'password', 'submit', 'image'):
            value = ''
            if input.has_attr('value'):
                value = input['value']
            if input.has_attr('name'):
                fields[input['name']] = value
            continue

        # checkboxes and radios
        if typ in ('checkbox', 'radio'):
            value = ''
            if input.has_attr('checked'):
                if input.has_attr('value'):
                    value = input['value']
                else:
                    value = 'on'
            if not input.has_attr('name'):
                continue
            if input['name']in fields and value:
                fields[input['name']] = value

            if input['name'] not in fields:
                fields[input['name']] = value

            continue

        assert False, 'input type %s not supported' % typ

    # textareas
    for textarea in soup.findAll('textarea'):
        fields[textarea['name']] = textarea.string or ''

    # select fields
    for select in soup.findAll('select'):
        value = ''
        options = select.findAll('option')
        is_multiple = select.has_attr('multiple')
        selected_options = [
            option for option in options
            if option.has_attr('selected')
        ]

        # If no select options, go with the first one
        if not selected_options and options:
            selected_options = [options[0]]

        if not is_multiple:
            assert(len(selected_options) < 2)
            if len(selected_options) == 1:
                value = selected_options[0]['value']
        else:
            value = [option['value'] for option in selected_options]

        if select.has_attr('name'):
            fields[select['name']] = value

    return fields

def findPageForm(content, url):
    retVal = list()
    page = BeautifulSoup(content, "html.parser")
    for form in page.find_all('form'):
        url = urljoin(url, form.get('action'))
        method = form.get('method', 'get')
        data = extract_form_fields(form)
        # very rare scenario but exists
        # I can't submit a form with one element named by 'submit'
        if "submit" in data:
            del data["submit"]
        if len(data) == 0:
            continue
        target = (url, method, data)
        retVal.append(target)
    return retVal