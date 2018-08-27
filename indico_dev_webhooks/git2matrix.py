import hashlib
import hmac
import re
import time

import requests
from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import Forbidden

from .util import Formatter, shorten_url


bp = Blueprint('git2matrix', __name__)
fmt = Formatter()


def matrix_post_msg(message):
    message_text = Formatter.strip(message)
    channel = current_app.config['MATRIX_CHANNEL']
    token = current_app.config['MATRIX_TOKEN']
    url = f'https://matrix.org/_matrix/client/r0/rooms/{channel}/send/m.room.message/f{int(time.time())}'
    payload = {
        'msgtype': 'm.text',
        'body': message_text,
        'format': 'org.matrix.custom.html',
        'formatted_body': message,
    }
    req = requests.put(url, params={'access_token': token}, json=payload)
    req.raise_for_status()


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
    payload = request.get_json()
    if request.headers.get('X-GitHub-Event') == 'push':
        github_push(payload)
    elif request.headers.get('X-GitHub-Event') == 'issues':
        github_issue(payload)
    elif request.headers.get('X-GitHub-Event') == 'pull_request':
        github_pull(payload)
    return jsonify()


def github_push(payload):
    repo_name = payload['repository']['name']
    pusher_name = payload['pusher']['name'] if payload.get('pusher') else 'somebody'
    created = payload['created'] or payload['before'] == '0'*40
    deleted = payload['deleted'] or payload['after'] == '0'*40
    forced = payload['forced']
    ref = payload['ref'] or ''
    base_ref = payload['base_ref'] or ''
    tag = ref.startswith('refs/tags/')
    ref_name = re.sub(r'\Arefs/(heads|tags)/', '', ref)
    tag_name = branch_name = ref_name
    base_ref_name = re.sub(r'\Arefs/(heads|tags)/', '', base_ref)
    before_sha = payload['before'][:6]
    after_sha = payload['after'][:6]
    commits = payload['commits']
    distinct_commits = [c for c in commits if c['distinct'] and c['message'].strip()]
    compare_url = payload['compare']
    repo_url = payload['repository']['url']
    branch_url = f'{repo_url}/commits/{branch_name}'
    before_sha_url = f'{repo_url}/commit/{before_sha}'

    def summary_url():
        if created:
            url = branch_url if not distinct_commits else compare_url
        elif deleted:
            url = before_sha_url
        elif forced:
            url = branch_url
        elif len(distinct_commits) == 1:
            url = distinct_commits[0]['url']
        else:
            url = compare_url
        return shorten_url(url)

    url = summary_url()

    def irc_push_summary_message():
        message = [f'[{fmt.repo(repo_name)}] {fmt.name(pusher_name)}']
        if created:
            if tag:
                message.append(f'tagged {fmt.tag(tag_name)} at')
                message.append(fmt.branch(base_ref_name) if base_ref else fmt.hash(after_sha))
            else:
                message.append(f'created {fmt.branch(branch_name)}')
                if base_ref:
                    message.append(f'from {fmt.branch(base_ref_name)}')
                elif not distinct_commits:
                    message.append(f'at {fmt.hash(after_sha)}')
                num = len(distinct_commits)
                message.append(f'({fmt.B(num)} new commit{"s" if num != 1 else ""})')
        elif deleted:
            message.append(f'{fmt.danger("deleted")} {fmt.branch(branch_name)} at {fmt.hash(before_sha)}')
        elif forced:
            message.append(f'{fmt.danger("force-pushed")} {fmt.branch(branch_name)} '
                           f'from {fmt.hash(before_sha)} to {fmt.hash(after_sha)}')
        elif commits and not distinct_commits:
            if base_ref:
                message.append(f'merged {fmt.branch(base_ref_name)} into {fmt.branch(branch_name)}')
            else:
                message.append(f'fast-forwarded {fmt.branch(branch_name)} '
                               f'from {fmt.hash(before_sha)} to {fmt.hash(after_sha)}')
        else:
            num = len(distinct_commits)
            message.append(f'pushed {fmt.B(num)} new commit{"s" if num != 1 else ""} to {fmt.branch(branch_name)}')
        return ' '.join(message)

    def irc_format_commit_message(commit):
        short = commit['message'].split('\n', 1)[0]
        if short != commit['message']:
            short += '...'
        author = commit['author']['name']
        sha1 = commit['id']
        return f"{fmt.repo(repo_name)}/{fmt.branch(branch_name)} {fmt.hash(sha1[:6])} {fmt.name(author)}: {short}"

    messages = [f'{irc_push_summary_message()}: {fmt.url(url)}']
    messages += [irc_format_commit_message(c) for c in distinct_commits[:3]]
    for message in messages:
        matrix_post_msg(message)


def github_issue(payload):
    action = payload['action']
    if action not in ('opened', 'closed', 'reopened'):
        return

    repo_name = payload['repository']['name']
    sender = payload['sender']['login']
    issue = payload['issue']
    number = issue['number']
    title = issue['title']
    url = shorten_url(issue['html_url'])

    message = f'[{fmt.repo(repo_name)}] {fmt.name(sender)} {action} issue #{number}: {fmt(title)}'
    matrix_post_msg(f'{message} {fmt.url(url)}')


def github_pull(payload):
    action = payload['action']
    if action not in ('opened', 'closed', 'reopened'):
        return

    repo_name = payload['repository']['name']
    sender = payload['sender']['login']
    pull = payload['pull_request']
    number = pull['number']
    title = pull['title']
    url = shorten_url(pull['html_url'])
    base_ref = pull['base']['label'].split(':')[-1]
    head_ref = pull['head']['label'].split(':')[-1]
    pretty_action = 'merged' if action == 'closed' and pull['merged'] else action
    message = (f'[{fmt.repo(repo_name)}] {fmt.name(sender)} {pretty_action} pull request #{number}: '
               f'{fmt(title)} ({fmt.branch(base_ref)}...{fmt.branch(head_ref)})')
    matrix_post_msg(f'{message} {fmt.url(url)}')
