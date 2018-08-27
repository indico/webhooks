import os
import sys

from flask import Flask

from .git2matrix import bp as git2matrix_bp


def configure_app(app):
    try:
        app.config['GITHUB_SECRET'] = os.environ['GITHUB_SECRET']
        app.config['MATRIX_TOKEN'] = os.environ['MATRIX_TOKEN']
        app.config['MATRIX_CHANNEL'] = os.environ['MATRIX_CHANNEL']
    except KeyError as exc:
        print(f'Required environment variable not set: {exc}')
        sys.exit(1)


app = Flask(__name__)
configure_app(app)
app.register_blueprint(git2matrix_bp, url_prefix='/git2matrix')


@app.route('/ping')
def ping():
    return '', 204


