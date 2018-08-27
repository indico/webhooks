import os
import sys
import time

import bleach
import markupsafe
import requests
from flask import Flask, jsonify, request


try:
    MATRIX_TOKEN = os.environ['MATRIX_TOKEN']
    MATRIX_CHANNEL = os.environ['MATRIX_CHANNEL']
except KeyError as exc:
    print(f'Required environment variable not set: {exc}')
    sys.exit(1)


def matrix_post_msg(message):
    url = f'https://matrix.org/_matrix/client/r0/rooms/{MATRIX_CHANNEL}/send/m.room.message/f{int(time.time())}'
    payload = {
        'msgtype': 'm.text',
        'body': bleach.clean(message, strip=True),
        'format': 'org.matrix.custom.html',
        'formatted_body': message,
    }
    requests.put(url, params={'access_token': MATRIX_TOKEN}, json=payload).raise_for_status()


app = Flask(__name__)


@app.route('/ping')
def ping():
    return '', 204


@app.route('/github')
def webhook_github():
    extra = markupsafe.escape(request.json['msg'])
    matrix_post_msg(f'This is just a <font color="red">test</font> - {extra}')
    return jsonify()
