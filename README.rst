=========================================
Proxmoxer: A wrapper for Proxmox REST API
=========================================

master branch:  |master_build_status| |master_coverage_status| |pypi_version| |pypi_downloads|

develop branch: |develop_build_status| |develop_coverage_status|


What does it do and what's different?
-------------------------------------

Proxmoxer is a wrapper around the `Proxmox REST API v2 <https://pve.proxmox.com/wiki/Proxmox_VE_API>`_.

It was inspired by slumber, but it dedicated only to Proxmox. It allows to use not only REST API over HTTPS, but
the same api over ssh and pvesh utility.

Like `Proxmoxia <https://github.com/baseblack/Proxmoxia>`_ it dynamically creates attributes which responds to the
attributes you've attempted to reach.

Installation
------------

.. code-block:: bash

    pip install proxmoxer

For 'https' backend install requests

.. code-block:: bash

    pip install requests

For 'ssh_paramiko' backend install paramiko

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

It is possible to use already prepared public/private key authentication. It is possible to use ssh-agent also.

.. code-block:: python

    from proxmoxer import ProxmoxAPI
    proxmox = ProxmoxAPI('proxmox_host', user='proxmox_admin', backend='ssh_paramiko')

**Please note, https-backend needs 'requests' library, ssh_paramiko-backend needs 'paramiko' library,
openssh-backend needs 'openssh_wrapper' library installed.**

Queries are exposed via the access methods **get**, **post**, **put** and **delete**. For convenience added two
synonyms: **create** for **post**, and **set** for **put**.

.. code-block:: python

    for node in proxmox.nodes.get():
        for vm in proxmox.nodes(node['node']).openvz.get():
            print "{0}. {1} => {2}" .format(vm['vmid'], vm['name'], vm['status'])

    >>> 141. puppet-2.london.baseblack.com => running
        101. munki.london.baseblack.com => running
        102. redmine.london.baseblack.com => running
        140. dns-1.london.baseblack.com => running
        126. ns-3.london.baseblack.com => running
        113. rabbitmq.london.baseblack.com => running

same code can be rewritten in the next way:

.. code-block:: python

    for node in proxmox.get('nodes'):
        for vm in proxmox.get('nodes/%s/openvz' % node['node']):
            print "%s. %s => %s" %  (vm['vmid'], vm['name'], vm['status'])


for example next lines do the same job:

.. code-block:: python

    proxmox.nodes(node['node']).openvz.get()
    proxmox.nodes(node['node']).get('openvz')
    proxmox.get('nodes/%s/openvz' % node['node'])
    proxmox.get('nodes', node['node'], 'openvz')


Some more examples:

.. code-block:: python

    for vm in proxmox.cluster.resources.get(type='vm'):
        print("{0}. {1} => {2}" .format(vm['vmid'], vm['name'], vm['status']))


.. code-block:: python

    node = proxmox.nodes('proxmox_node')
    pprint(node.storage('local').content.get())

or the with same results

.. code-block:: python

    node = proxmox.nodes.proxmox_node()
    pprint(node.storage.local.content.get())


Example of creation of lxc container:

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

Example of template upload:

.. code-block:: python

    local_storage = proxmox.nodes('proxmox_node').storage('local')
    local_storage.upload.create(content='vztmpl',
        filename=open(os.path.expanduser('~/templates/debian-6-my-core_1.0-1_i386.tar.gz'))))


Example of rrd download:

.. code-block:: python

    response = proxmox.nodes('proxmox').rrd.get(ds='cpu', timeframe='hour')
    with open('cpu.png', 'wb') as f:
        f.write(response['image'].encode('raw_unicode_escape'))

Example of usage of logging:

.. code-block:: python

    # now logging debug info will be written to stdout
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(name)s: %(message)s')


Roadmap
-------

* write tests
* support other actual python versions
* add optional validation of requests
* add some shortcuts for convenience

History
-------

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

.. |master_build_status| image:: https://travis-ci.org/swayf/proxmoxer.png?branch=master
    :target: https://travis-ci.org/swayf/proxmoxer

.. |master_coverage_status| image:: https://coveralls.io/repos/swayf/proxmoxer/badge.png?branch=master
    :target: https://coveralls.io/r/swayf/proxmoxer

.. |develop_build_status| image:: https://travis-ci.org/swayf/proxmoxer.png?branch=develop
    :target: https://travis-ci.org/swayf/proxmoxer

.. |develop_coverage_status| image:: https://coveralls.io/repos/swayf/proxmoxer/badge.png?branch=develop
    :target: https://coveralls.io/r/swayf/proxmoxer

.. |pypi_version| image:: https://img.shields.io/pypi/v/proxmoxer.svg
    :target: https://pypi.python.org/pypi/proxmoxer

.. |pypi_downloads| image:: https://img.shields.io/pypi/dm/proxmoxer.svg
    :target: https://pypi.python.org/pypi/proxmoxer

