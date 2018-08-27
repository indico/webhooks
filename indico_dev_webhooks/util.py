import re

import requests
from markupsafe import Markup, escape


class Formatter:
    _colors = {
        'url': 'teal',
        'repo': 'lime',
        'name': 'lightgrey',
        'branch': 'orange',
        'tag': 'yellow',
        'hash': 'gray',
        'danger': 'red',
    }
    _tags = {
        'B': 'b',
    }

    def __getattr__(self, name):
        if name.isupper():
            def fn(text):
                return Markup(f'<{self._tags[name]}>{{}}</{self._tags[name]}>').format(text)
        else:
            def fn(text):
                return Markup(f'<font color="{self._colors[name]}">{{}}</font>').format(text)
        return fn

    def __call__(self, msg):
        return escape(msg)

    @staticmethod
    def strip(msg):
        msg = re.sub(r'</?b>|</font>|<font color="[^"]+">', '', msg)
        # invert markupsafe.escape()
        return (msg
                .replace('&amp;', '&')
                .replace('&gt;', '>')
                .replace('&lt;', '<')
                .replace('&#39;', "'")
                .replace('&#34;', '"'))


def shorten_url(url):
    return 'https://git.io/DUMMY'  # TODO remove this
    try:
        req = requests.post('https://git.io', data={'url': url}, allow_redirects=False)
    except requests.RequestException:
        return url
    if req.status_code == 201:
        return req.headers['Location']
    return url
