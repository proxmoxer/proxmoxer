=========================================
Proxmoxer: A Python wrapper for Proxmox REST API
=========================================

master branch:  |master_build_status| |master_coverage_status| |pypi_version| |pypi_downloads|

develop branch: |develop_build_status| |develop_coverage_status|


Proxmoxer is a python wrapper around the `Proxmox REST API v2 <https://pve.proxmox.com/pve-docs/api-viewer/index.html>`_.
It currently supports the Proxmox services of Proxmox Virtual Environment (PVE), Proxmox Mail Gateway (PMG), and Proxmox Backup Server (PBS).

It was inspired by slumber, but it is dedicated only to Proxmox. It allows not only REST API use over HTTPS, but
the same api over ssh and pvesh utility.

Like `Proxmoxia <https://github.com/baseblack/Proxmoxia>`_, it dynamically creates attributes which responds to the
attributes you've attempted to reach.

Full Documentation is available at https://proxmoxer.github.io/docs/
--------------------------------------------------------------------

Installation
............

.. code-block:: bash

    pip install proxmoxer

To use the 'https' backend, install requests

.. code-block:: bash

    pip install requests

To use the 'ssh_paramiko' backend, install paramiko

.. code-block:: bash

    pip install paramiko

To use the 'openssh' backend, install openssh_wrapper

.. code-block:: bash

    pip install openssh_wrapper


Short usage information
.......................

The first thing to do is import the proxmoxer library and create ProxmoxAPI instance.

.. code-block:: python

    from proxmoxer import ProxmoxAPI

    proxmox = ProxmoxAPI(
        "proxmox_host", user="admin@pam", password="secret_word", verify_ssl=False
    )

This will connect by default to PVE through the 'https' backend.

**Note: ensure you have the required libraries (listed above) for the connection method you are using**

Queries are exposed via the access methods **get**, **post**, **put** and **delete**. For convenience two
synonyms are available: **create** for **post**, and **set** for **put**.

Using the paths from the `PVE API v2 <https://pve.proxmox.com/pve-docs/api-viewer/index.html>`_, you can create
API calls using the access methods above.

.. code-block:: pycon

    >>> for node in proxmox.nodes.get():
    ...     for vm in proxmox.nodes(node["node"]).openvz.get():
    ...         print "{0}. {1} => {2}".format(vm["vmid"], vm["name"], vm["status"])
    ...

    141. puppet-2.london.example.com => running
    101. munki.london.example.com => running
    102. redmine.london.example.com => running
    140. dns-1.london.example.com => running
    126. ns-3.london.example.com => running
    113. rabbitmq.london.example.com => running


See Changelog in `CHANGELOG.md <https://github.com/proxmoxer/proxmoxer/blob/develop/CHANGELOG.md>`_
...................................................................................................

.. |master_build_status| image:: https://github.com/proxmoxer/proxmoxer/actions/workflows/ci.yaml/badge.svg?branch=master
    :target: https://github.com/proxmoxer/proxmoxer/actions

.. |master_coverage_status| image:: https://img.shields.io/coveralls/github/proxmoxer/proxmoxer/master
    :target: https://coveralls.io/github/proxmoxer/proxmoxer?branch=master

.. |develop_build_status| image:: https://github.com/proxmoxer/proxmoxer/actions/workflows/ci.yaml/badge.svg?branch=develop
    :target: https://github.com/proxmoxer/proxmoxer/actions

.. |develop_coverage_status| image:: https://img.shields.io/coveralls/github/proxmoxer/proxmoxer/develop
    :target: https://coveralls.io/github/proxmoxer/proxmoxer?branch=develop

.. |pypi_version| image:: https://img.shields.io/pypi/v/proxmoxer.svg
    :target: https://pypi.python.org/pypi/proxmoxer

.. |pypi_downloads| image:: https://img.shields.io/pypi/dm/proxmoxer.svg
    :target: https://pypi.python.org/pypi/proxmoxer
