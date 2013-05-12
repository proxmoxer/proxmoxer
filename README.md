## Proxmoxer: A wrapper for Proxmox REST API v2

## What does it do and what's different?

Proxmoxer is a wrapper around the [Proxmox REST API v2](http://pve.proxmox.com/pve2-api-doc/).

It was inspired by slumber, but extended a little bit for Proxmox. It allows to use not only HTTPS REST API, but
the same api over ssh and pvesh utility.

Like [Proxmoxia](https://github.com/baseblack/Proxmoxia) it dynamically creates attributes  which responds to the
attributes you've attempted to reach. In many ways this proxmoxer lib is compatible with code for Proxmoxia.


##Short usage information

The first thing to do is import the proxmoxer library and create ProxmoxAPI instance.

```python
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI('proxmox_host', user='admin@pam', password='secret_word', verify_ssl=False)

```
This will connect by default through the 'https' backend.

It is possible to use already prepared public/private key authentication. It is possible to use ssh-agent also.

```python
from proxmoxer import ProxmoxAPI

proxmox = ProxmoxAPI('proxmox_host', user='proxmox_admin', backend='ssh_paramiko')

```

Please note, https-backend needs 'requests' library, and ssh_paramiko-backend needs 'paramiko' library installed.


Queries are exposed via the access methods **get**, **post**, **put** and **delete**. For convenience added two
synonym: *create* for *post*, and *set* for *put*.

```python
for node in proxmox.nodes.get():
    for vm in proxmox.nodes(node['node']).openvz.get()):
        print "{0}. {1} => {2}" .format(vm['vmid'], vm['name'], vm['status'])

>>> 141. puppet-2.london.baseblack.com => running
    101. munki.london.baseblack.com => running
    102. redmine.london.baseblack.com => running
    140. dns-1.london.baseblack.com => running
    126. ns-3.london.baseblack.com => running
    113. rabbitmq.london.baseblack.com => running
```
same code can be rewritten in the next way:

```python
for node in proxmox.get('nodes'):
    for vm in proxmox.get('nodes/%s/openvz' % node['node']):
        print "%s. %s => %s" %  (vm['vmid'], vm['name'], vm['status'])
```

for example next lines do the same job:

```python
proxmox.nodes(node['node']).openvz.get()
proxmox.nodes(node['node']).get('openvz')
proxmox.get('nodes/%s/openvz' % node['node'])
proxmox.get('nodes', node['node'], 'openvz')

```

Some more examples:

```python
node = proxmox.nodes('proxmox_node')
pprint(node.storage('local').content.get())
```
or the with same results
```python
node = proxmox.nodes.proxmox_node()
pprint(node.storage.local.content.get())
```

Example of creation of openvz container:
```python
node = proxmox.nodes('proxmox_node')
node.openvz.create(vmid=202,
                   ostemplate='local:vztmpl/debian-6-turnkey-core_12.0-1_i386.tar.gz',
                   hostname='turnkey',
                   storage='local',
                   memory=512,
                   swap=512,
                   cpus=1,
                   disk=4,
                   password='secret',
                   ip_address='10.0.0.202')
```

Example of template upload:
```python
local_storage = proxmox.nodes('proxmox_node').storage('local')
local_storage.upload.create(content='vztmpl',
                            filename=open(os.path.expanduser('~/templates/debian-6-my-core_1.0-1_i386.tar.gz'))))
```

Example of rrd download:
```python
response = proxmox.nodes('proxmox').rrd.get(ds='cpu', timeframe='hour')
with open('cpu.png', 'wb') as f:
    f.write(response['image'].encode('raw_unicode_escape'))
```

# Roadmap
- write tests
- add optional validation of requests
- add some shortcuts for convenience