=========================================
Proxmoxer: A wrapper for Proxmox REST API
=========================================

master branch:  |master_build_status| |master_coverage_status| |pypi_version| |pypi_downloads|

develop branch: |develop_build_status| |develop_coverage_status|


What does it do and what's different?
-------------------------------------

Proxmoxer is a wrapper around the `Proxmox REST API v2 <https://pve.proxmox.com/pve-docs/api-viewer/index.html>`_.

It was inspired by slumber, but it is dedicated only to Proxmox. It allows not only REST API use over HTTPS, but
the same api over ssh and pvesh utility.

Like `Proxmoxia <https://github.com/baseblack/Proxmoxia>`_, it dynamically creates attributes which responds to the
attributes you've attempted to reach.

Installation
------------

.. code-block:: bash

    pip install proxmoxer

To use the 'https' backend, install requests

.. code-block:: bash

    pip install requests

To use the 'ssh_paramiko' backend, install paramiko

.. code-block:: bash

    pip install paramiko


Short usage information
-----------------------

The first thing to do is import the proxmoxer library and create ProxmoxAPI instance.

.. code-block:: python

    from proxmoxer import ProxmoxAPI
    proxmox = ProxmoxAPI('proxmox_host', user='admin@pam',
                         password='secret_word', verify_ssl=False)

This will connect by default through the 'https' backend.

You can also setup `API Tokens <https://pve.proxmox.com/wiki/User_Management#pveum_tokens>`_ which allow tighter access controls.
API Tokens are also stateless, so they much better for long-lived programs that might have the standard username/password authentication timeout.
API tokens can be created through the web UI or through the `API <https://pve.proxmox.com/pve-docs/api-viewer/index.html#/access/users/{userid}/token/{tokenid}>`_.

.. code-block:: python

    from proxmoxer import ProxmoxAPI
    proxmox = ProxmoxAPI('proxmox_host', user='admin', token_name='test_token', token_value='ab27beeb-9ac4-4df1-aa19-62639f27031e')

For SSH access, it is possible to use pre-prepared public/private key authentication and ssh-agent.

.. code-block:: python

    from proxmoxer import ProxmoxAPI
    proxmox = ProxmoxAPI('proxmox_host', user='proxmox_admin', backend='ssh_paramiko')

**Note: the 'https' backend needs the 'requests' library, the 'ssh_paramiko' backend needs the 'paramiko' library,
and the 'openssh' backend needs the 'openssh_wrapper' library installed.**

Queries are exposed via the access methods **get**, **post**, **put** and **delete**. For convenience two
synonyms are available: **create** for **post**, and **set** for **put**.

Using the paths from the `Proxmox REST API v2 <https://pve.proxmox.com/pve-docs/api-viewer/index.html>`_, you can create
API calls using the access methods above.

.. code-block:: python

    for node in proxmox.nodes.get():
        for vm in proxmox.nodes(node['node']).openvz.get():
            print "{0}. {1} => {2}" .format(vm['vmid'], vm['name'], vm['status'])

    >>> 141. puppet-2.london.example.com => running
        101. munki.london.example.com => running
        102. redmine.london.example.com => running
        140. dns-1.london.example.com => running
        126. ns-3.london.example.com => running
        113. rabbitmq.london.example.com => running

same code can be rewritten in the next way:

.. code-block:: python

    for node in proxmox.get('nodes'):
        for vm in proxmox.get('nodes/%s/openvz' % node['node']):
            print "%s. %s => %s" %  (vm['vmid'], vm['name'], vm['status'])


As a demonstration of the flexibility of usage of this library, the following lines accomplish the equivalent function:

.. code-block:: python

    proxmox.nodes(node['node']).openvz.get()
    proxmox.nodes(node['node']).get('openvz')
    proxmox.get('nodes/%s/openvz' % node['node'])
    proxmox.get('nodes', node['node'], 'openvz')


Some more examples:

Listing VMs:
.. code-block:: python

    for vm in proxmox.cluster.resources.get(type='vm'):
        print("{0}. {1} => {2}" .format(vm['vmid'], vm['name'], vm['status']))

Listing contents of the ``local`` storage on the ``proxmox_node`` node (method 1):
.. code-block:: python

    node = proxmox.nodes('proxmox_node')
    pprint(node.storage('local').content.get())

Listing contents of the ``local`` storage on the ``proxmox_node`` node (method 2):
.. code-block:: python

    node = proxmox.nodes.proxmox_node()
    pprint(node.storage.local.content.get())


creating a new lxc container:

.. code-block:: python

    node = proxmox.nodes('proxmox_node')
    node.lxc.create(vmid=202,
        ostemplate='local:vztmpl/debian-9.0-standard_20170530_amd64.tar.gz',
        hostname='debian-stretch',
        storage='local',
        memory=512,
        swap=512,
        cores=1,
        password='secret',
        net0='name=eth0,bridge=vmbr0,ip=192.168.22.1/20,gw=192.168.16.1')

The same lxc container can be created with options set in a dictionary.
This approach allows adding ``ssh-public-keys`` without getting syntax errors.

.. code-block:: python

    newcontainer = { 'vmid': 202,
        'ostemplate': 'local:vztmpl/debian-9.0-standard_20170530_amd64.tar.gz',
        'hostname': 'debian-stretch',
        'storage': 'local',
        'memory': 512,
        'swap': 512,
        'cores': 1,
        'password': 'secret',
        'net0': 'name=eth0,bridge=vmbr0,ip=192.168.22.1/20,gw=192.168.16.1' }
    node = proxmox.nodes('proxmox_node')
    node.lxc.create(**newcontainer)

Uploading a template:

.. code-block:: python

    local_storage = proxmox.nodes('proxmox_node').storage('local')
    local_storage.upload.create(content='vztmpl',
        filename=open(os.path.expanduser('~/templates/debian-6-my-core_1.0-1_i386.tar.gz'))))


Downloading rrd CPU image data to a file:

.. code-block:: python

    response = proxmox.nodes('proxmox').rrd.get(ds='cpu', timeframe='hour')
    with open('cpu.png', 'wb') as f:
        f.write(response['image'].encode('raw_unicode_escape'))

Example of usage of logging:

.. code-block:: python

    # now logging debug info will be written to stdout
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(name)s: %(message)s')


Changelog
---------

1.1.0 (2020-05-22)
..................
* Addition (https): Added API Token authentication (`John Hollowell <https://github.com/jhollowe>`_)
* Improvement (https): user/password authentication refreshes ticket to prevent expiration (`CompileNix <https://github.com/compilenix>`_ and `John Hollowell <https://github.com/jhollowe>`_)
* Bugfix (ssh_paramiko): Handle empty stderr from ssh connections (`morph027 <https://github.com/morph027>`_)
* DEPRECATED (https): using ``auth_token`` and ``csrf_token`` (ProxmoxHTTPTicketAuth) is now deprecated. Either pass the ``auth_token`` as the ``password`` or use the API Tokens.

1.0.4 (2020-01-24)
..................
* Improvement (https): Added timeout to authentication (James Lin)
* Improvement (https): Handle AnyEvent::HTTP status codes gracefully (Georges Martin)
* Improvement (https): Advanced error message with error code >=400 (`ssi444 <https://github.com/ssi444>`_)
* Bugfix (ssh): Fix pvesh output format for version > 5.3 (`timansky <https://github.com/timansky>`_)
* Transfered development to proxmoxer organization

1.0.3 (2018-09-10)
..................
* Improvement: Added option to specify port in hostname parameter (`pvanagtmaal <https://github.com/pvanagtmaal>`_)
* Improvement: Added stderr to the Response content (`Jérôme Schneider <https://github.com/merinos>`_)
* Bugfix: Paramiko python3: stdout and stderr must be a str not bytes (`Jérôme Schneider <https://github.com/merinos>`_)
* New lxc example in docu (`Geert Stappers <https://github.com/stappersg>`_)

1.0.2 (2017-12-02)
..................
* Tarball repackaged with tests

1.0.1 (2017-12-02)
..................
* LICENSE file now included in tarball
* Added verify_ssl parameter to ProxmoxHTTPAuth (`Walter Doekes <https://github.com/wdoekes>`_)

1.0.0 (2017-11-12)
..................
* Update Proxmoxer readme (`Emmanuel Kasper <https://github.com/EmmanuelKasper>`_)
* Display the reason of API calls errors (`Emmanuel Kasper <https://github.com/EmmanuelKasper>`_, `kantsdog <https://github.com/kantsdog>`_)
* Filter for ssh response code (`Chris Plock <https://github.com/chrisplo>`_)

0.2.5 (2017-02-12)
..................
* Adding sudo to execute CLI with paramiko ssh backend (`Jason Meridth <https://github.com/jmeridth>`_)
* Proxmoxer/backends/ssh_paramiko: improve file upload (`Jérôme Schneider <https://github.com/merinos>`_)

0.2.4 (2016-05-02)
..................
* Removed newline in tmp_filename string (`Jérôme Schneider <https://github.com/merinos>`_)
* Fix to avoid module reloading (`jklang <https://github.com/jklang>`_)

0.2.3 (2016-01-20)
..................
* Minor typo fix (`Srinivas Sakhamuri <https://github.com/srsakhamuri>`_)

0.2.2 (2016-01-19)
..................
* Adding sudo to execute pvesh CLI in openssh backend (`Wei Tie <https://github.com/TieWei>`_, `Srinivas Sakhamuri <https://github.com/srsakhamuri>`_)
* Add support to specify an identity file for ssh connections (`Srinivas Sakhamuri <https://github.com/srsakhamuri>`_)

0.2.1 (2015-05-02)
..................
* fix for python 3.4 (`kokuev <https://github.com/kokuev>`_)

0.2.0 (2015-03-21)
..................
* Https will now raise AuthenticationError when appropriate. (`scap1784 <https://github.com/scap1784>`_)
* Preliminary python 3 compatibility. (`wdoekes <https://github.com/wdoekes>`_)
* Additional example. (`wdoekes <https://github.com/wdoekes>`_)

0.1.7 (2014-11-16)
..................
* Added ignore of "InsecureRequestWarning: Unverified HTTPS request is being made..." warning while using https (requests) backend.

0.1.4 (2013-06-01)
..................
* Added logging
* Added openssh backend
* Tests are reorganized

0.1.3 (2013-05-30)
..................
* Added next tests
* Bugfixes

0.1.2 (2013-05-27)
..................
* Added first tests
* Added support for travis and coveralls
* Bugfixes

0.1.1 (2013-05-13)
..................
* Initial try.

.. |master_build_status| image:: https://travis-ci.org/proxmoxer/proxmoxer.png?branch=master
    :target: https://travis-ci.org/proxmoxer/proxmoxer

.. |master_coverage_status| image:: https://coveralls.io/repos/proxmoxer/proxmoxer/badge.png?branch=master
    :target: https://coveralls.io/r/proxmoxer/proxmoxer

.. |develop_build_status| image:: https://travis-ci.org/proxmoxer/proxmoxer.png?branch=develop
    :target: https://travis-ci.org/proxmoxer/proxmoxer

.. |develop_coverage_status| image:: https://coveralls.io/repos/proxmoxer/proxmoxer/badge.png?branch=develop
    :target: https://coveralls.io/r/proxmoxer/proxmoxer

.. |pypi_version| image:: https://img.shields.io/pypi/v/proxmoxer.svg
    :target: https://pypi.python.org/pypi/proxmoxer

.. |pypi_downloads| image:: https://img.shields.io/pypi/dm/proxmoxer.svg
    :target: https://pypi.python.org/pypi/proxmoxer
