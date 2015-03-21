#!/usr/bin/env python
import codecs
import re
import sys
import proxmoxer
import os
from setuptools import setup


if not os.path.exists('README.txt') and 'sdist' in sys.argv:
    with codecs.open('README.rst', encoding='utf8') as f:
        rst = f.read()
    code_block = '(:\n\n)?\.\. code-block::.*'
    rst = re.sub(code_block, '::', rst)
    with codecs.open('README.txt', encoding='utf8', mode='wb') as f:
        f.write(rst)


try:
    readme = 'README.txt' if os.path.exists('README.txt') else 'README.rst'
    long_description = codecs.open(readme, encoding='utf-8').read()
except:
    long_description = 'Could not read README.txt'


setup(
    name = 'proxmoxer',
    version = proxmoxer.__version__,
    description = 'Python Wrapper for the Proxmox 2.x API (HTTP and SSH)',
    author = 'Oleg Butovich',
    author_email = 'obutovich@gmail.com',
    license = "MIT",
    url = 'https://github.com/swayf/proxmoxer',
    download_url = 'http://pypi.python.org/pypi/proxmoxer',
    keywords = ['proxmox', 'api'],
    packages=['proxmoxer', 'proxmoxer.backends'],
    classifiers = [ #http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    long_description = long_description
)
