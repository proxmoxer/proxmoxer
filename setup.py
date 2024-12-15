#!/usr/bin/env python
import codecs
import os
import re
import sys

from setuptools import setup

from proxmoxer import __version__ as proxmoxer_version

if not os.path.exists("README.txt") and "sdist" in sys.argv:
    with codecs.open("README.rst", encoding="utf8") as f:
        rst = f.read()
    code_block = r"(:\n\n)?\.\. code-block::.*"
    rst = re.sub(code_block, "::", rst)
    with codecs.open("README.txt", encoding="utf8", mode="wb") as f:
        f.write(rst)


try:
    readme = "README.txt" if os.path.exists("README.txt") else "README.rst"
    long_description = codecs.open(readme, encoding="utf-8").read()
except IOError:
    long_description = "Could not read README.txt"


setup(
    name="proxmoxer",
    version=proxmoxer_version,
    description="Python Wrapper for the Proxmox 2.x API (HTTP and SSH)",
    author="Oleg Butovich",
    author_email="obutovich@gmail.com",
    license="MIT",
    url="https://proxmoxer.github.io/docs/",
    download_url="http://pypi.python.org/pypi/proxmoxer",
    keywords=["proxmox", "api"],
    packages=["proxmoxer", "proxmoxer.backends", "proxmoxer.tools"],
    classifiers=[  # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Clustering",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    long_description=long_description,
    long_description_content_type="text/x-rst",
)
