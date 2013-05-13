#!/usr/bin/env python
import codecs
import re
import proxmoxer

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def long_description():
    """Pre-process the README so that PyPi can render it properly."""
    with codecs.open('README.rst', encoding='utf8') as f:
        rst = f.read()
    code_block = '(:\n\n)?\.\. code-block::.*'
    rst = re.sub(code_block, '::', rst)
    return rst

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
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    long_description = long_description()
)