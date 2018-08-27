from __future__ import unicode_literals

from setuptools import find_packages, setup

setup(
    name='indico-dev-webhooks',
    version='1.0',
    url='https://github.com/indico/webhooks',
    license='MIT',
    author='Adrian Moennich',
    author_email='adrian.moennich@cern.ch',
    description='Indico dev webhooks',
    packages=find_packages(),
    zip_safe=False,
    install_requires=['bleach', 'flask', 'requests', 'gunicorn', 'markupsafe'],
)
