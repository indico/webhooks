import time

import bleach
import markupsafe
import requests
from flask import Blueprint, current_app, jsonify, request


bp = Blueprint('git2matrix', __name__)


def matrix_post_msg(message):
    channel = current_app.config['MATRIX_CHANNEL']
    token = current_app.config['MATRIX_TOKEN']
    url = f'https://matrix.org/_matrix/client/r0/rooms/{channel}/send/m.room.message/f{int(time.time())}'
    payload = {
        'msgtype': 'm.text',
        'body': bleach.clean(message, strip=True),
        'format': 'org.matrix.custom.html',
        'formatted_body': message,
    }
    requests.put(url, params={'access_token': token}, json=payload).raise_for_status()


@bp.route('/github')
def webhook_github():
    extra = markupsafe.escape(request.json['msg'])
    matrix_post_msg(f'This is just a <font color="red">test</font> - {extra}')
    return jsonify()
