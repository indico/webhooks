import hashlib
import hmac
import time

import bleach
import requests
from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import Forbidden


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


def verify_github_signature():
    signature = request.headers.get('X-Hub-Signature', '')
    data = request.get_data()
    github_secret = bytes(current_app.config['GITHUB_SECRET'], 'UTF-8')
    mac = hmac.new(github_secret, msg=data, digestmod=hashlib.sha1).hexdigest()
    return hmac.compare_digest(f'sha1={mac}', signature)


@bp.route('/github', methods=('POST',))
def webhook_github():
    if not verify_github_signature():
        raise Forbidden('Signature invalid')
    if request.headers.get('X-GitHub-Event') == 'ping':
        print('ping', request.json)
    elif request.headers.get('X-GitHub-Event') == 'push':
        print('push', request.json)
    return jsonify()
