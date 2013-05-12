#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name = 'proxmoxer',
    version = '0.1.0',
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
    long_description = """
A python wrapper for the Proxmox 2.x API.

Usage example:

1) Create an instance of the ProxmoxAPI class by passing in the
url or ip of a server, backend, username (and password if it is needed):

proxmox = ProxmoxAPI('node01.example.org', user='user@pve', password='secretPassword')
or
proxmox = ProxmoxAPI('node01.example.org', user='admin')

2) Call methods according http://pve.proxmox.com/pve2-api-doc/ like:

node = p.nodes('node01')
node.openvz.create(vmid=800,
                   ostemplate='local:vztmpl/debian-6-turnkey-core_12.0-1_i386.tar.gz',
                   hostname='test_host',
                   storage='local',
                   memory=512,
                   swap=512,
                   cpus=1,
                   disk=4,
                   password='secret',
                   ip_address='10.0.0.100')
resources = p.cluster.resources.get()

For more information see http://pypi.python.org/pypi/proxmoxer
"""
)