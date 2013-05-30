from itertools import izip, islice
import unittest
from mock import patch, MagicMock
from nose.tools import eq_, ok_
from proxmoxer import ProxmoxAPI


@patch('requests.sessions.Session')
def test_https_connection(req_session):
    response = {'ticket': 'ticket',
                'CSRFPreventionToken': 'CSRFPreventionToken'}
    req_session.request.return_value = response
    ProxmoxAPI('proxmox', user='root@pam', password='secret', port=123, verify_ssl=False)
    call = req_session.return_value.request.call_args[1]
    eq_(call['url'], 'https://proxmox:123/api2/json/access/ticket')
    eq_(call['data'], {'username': 'root@pam', 'password': 'secret'})
    eq_(call['method'], 'post')
    eq_(call['verify'], False)


class TestSuite(unittest.TestCase):
    proxmox = None
    serializer = None
    session = None

    # noinspection PyMethodOverriding
    @patch('requests.sessions.Session')
    def setUp(self, session):
        response = {'ticket': 'ticket',
                    'CSRFPreventionToken': 'CSRFPreventionToken'}
        session.request.return_value = response
        self.proxmox = ProxmoxAPI('proxmox', user='root@pam', password='secret', port=123, verify_ssl=False)
        self.serializer = MagicMock()
        self.session = MagicMock()
        self.session.request.return_value.status_code = 200
        self.proxmox._store['session'] = self.session
        self.proxmox._store['serializer'] = self.serializer

    def test_get(self):
        self.proxmox.nodes('proxmox').storage('local').get()
        eq_(self.session.request.call_args[0], ('GET', 'https://proxmox:123/api2/json/nodes/proxmox/storage/local'))

    def test_delete(self):
        self.proxmox.nodes('proxmox').openvz(100).delete()
        eq_(self.session.request.call_args[0], ('DELETE', 'https://proxmox:123/api2/json/nodes/proxmox/openvz/100'))
        self.proxmox.nodes('proxmox').openvz('101').delete()
        eq_(self.session.request.call_args[0], ('DELETE', 'https://proxmox:123/api2/json/nodes/proxmox/openvz/101'))

    def test_post(self):
        node = self.proxmox.nodes('proxmox')
        node.openvz.create(vmid=800,
                           ostemplate='local:vztmpl/debian-6-turnkey-core_12.0-1_i386.tar.gz',
                           hostname='test',
                           storage='local',
                           memory=512,
                           swap=512,
                           cpus=1,
                           disk=4,
                           password='secret',
                           ip_address='10.0.100.222')
        eq_(self.session.request.call_args[0], ('POST', 'https://proxmox:123/api2/json/nodes/proxmox/openvz'))
        ok_('data' in self.session.request.call_args[1])
        data = self.session.request.call_args[1]['data']
        eq_(data['cpus'], 1)
        eq_(data['disk'], 4)
        eq_(data['hostname'], 'test')
        eq_(data['ip_address'], '10.0.100.222')
        eq_(data['memory'], 512)
        eq_(data['ostemplate'], 'local:vztmpl/debian-6-turnkey-core_12.0-1_i386.tar.gz')
        eq_(data['password'], 'secret')
        eq_(data['storage'], 'local')
        eq_(data['swap'], 512)
        eq_(data['vmid'], 800)

        node = self.proxmox.nodes('proxmox1')
        node.openvz.post(vmid=900,
                         ostemplate='local:vztmpl/debian-7-turnkey-core_12.0-1_i386.tar.gz',
                         hostname='test1',
                         storage='local1',
                         memory=1024,
                         swap=1024,
                         cpus=2,
                         disk=8,
                         password='secret1',
                         ip_address='10.0.100.111')
        eq_(self.session.request.call_args[0], ('POST', 'https://proxmox:123/api2/json/nodes/proxmox1/openvz'))
        ok_('data' in self.session.request.call_args[1])
        data = self.session.request.call_args[1]['data']
        eq_(data['cpus'], 2)
        eq_(data['disk'], 8)
        eq_(data['hostname'], 'test1')
        eq_(data['ip_address'], '10.0.100.111')
        eq_(data['memory'], 1024)
        eq_(data['ostemplate'], 'local:vztmpl/debian-7-turnkey-core_12.0-1_i386.tar.gz')
        eq_(data['password'], 'secret1')
        eq_(data['storage'], 'local1')
        eq_(data['swap'], 1024)
        eq_(data['vmid'], 900)

    def test_put(self):
        node = self.proxmox.nodes('proxmox')
        node.openvz(101).config.set(cpus=4, memory=1024, ip_address='10.0.100.100', onboot=True)
        eq_(self.session.request.call_args[0], ('PUT', 'https://proxmox:123/api2/json/nodes/proxmox/openvz/101/config'))
        data = self.session.request.call_args[1]['data']
        eq_(data['cpus'], 4)
        eq_(data['memory'], 1024)
        eq_(data['ip_address'], '10.0.100.100')
        eq_(data['onboot'], True)

        node = self.proxmox.nodes('proxmox1')
        node.openvz(102).config.put(cpus=2, memory=512, ip_address='10.0.100.200', onboot=False)
        eq_(self.session.request.call_args[0],
            ('PUT', 'https://proxmox:123/api2/json/nodes/proxmox1/openvz/102/config'))
        data = self.session.request.call_args[1]['data']
        eq_(data['cpus'], 2)
        eq_(data['memory'], 512)
        eq_(data['ip_address'], '10.0.100.200')
        eq_(data['onboot'], False)


@patch('paramiko.SSHClient')
def test_paramiko_connection(_):
    proxmox = ProxmoxAPI('proxmox', user='root', backend='ssh_paramiko', port=123)
    session = proxmox._store['session']
    eq_(session.ssh_client.connect.call_args[0], ('proxmox',))
    eq_(session.ssh_client.connect.call_args[1], {'username': 'root',
                                                  'allow_agent': True,
                                                  'key_filename': None,
                                                  'look_for_keys': True,
                                                  'timeout': 5,
                                                  'password': None,
                                                  'port': 123})


class TestParamikoSuite(unittest.TestCase):
    proxmox = None
    client = None

    # noinspection PyMethodOverriding
    @patch('paramiko.SSHClient')
    def setUp(self, ssh_client):
        self.proxmox = ProxmoxAPI('proxmox', user='root', backend='ssh_paramiko', port=123)
        self.client = self.proxmox._store['session'].ssh_client
        self.session = self.client.get_transport().open_session()
        self.session.makefile_stderr.return_value = ['200 OK']

    def _split_cmd(self, cmd):
        splitted = cmd.split()
        eq_(splitted[0], 'pvesh')
        options_set = set((' '.join((k, v)) for k, v in
                           izip(islice(splitted, 3, None, 2), islice(splitted, 4, None, 2))))
        return ' '.join(splitted[1:3]), options_set

    def test_get(self):
        self.session.makefile.return_value = ["""
            [
               {
                  "subdir" : "status"
               },
               {
                  "subdir" : "content"
               },
               {
                  "subdir" : "upload"
               },
               {
                  "subdir" : "rrd"
               },
               {
                  "subdir" : "rrddata"
               }
            ]"""]
        result = self.proxmox.nodes('proxmox').storage('local').get()
        eq_(self.session.exec_command.call_args[0], ('pvesh get /nodes/proxmox/storage/local',))
        eq_(result[0]['subdir'], 'status')
        eq_(result[1]['subdir'], 'content')
        eq_(result[2]['subdir'], 'upload')
        eq_(result[3]['subdir'], 'rrd')
        eq_(result[4]['subdir'], 'rrddata')

    def test_delete(self):
        self.proxmox.nodes('proxmox').openvz(100).delete()
        eq_(self.session.exec_command.call_args[0], ('pvesh delete /nodes/proxmox/openvz/100',))
        self.proxmox.nodes('proxmox').openvz('101').delete()
        eq_(self.session.exec_command.call_args[0], ('pvesh delete /nodes/proxmox/openvz/101',))
        self.proxmox.nodes('proxmox').openvz.delete('102')
        eq_(self.session.exec_command.call_args[0], ('pvesh delete /nodes/proxmox/openvz/102',))

    def test_post(self):
        node = self.proxmox.nodes('proxmox')
        node.openvz.create(vmid=800,
                           ostemplate='local:vztmpl/debian-6-turnkey-core_12.0-1_i386.tar.gz',
                           hostname='test',
                           storage='local',
                           memory=512,
                           swap=512,
                           cpus=1,
                           disk=4,
                           password='secret',
                           ip_address='10.0.100.222')
        cmd, options = self._split_cmd(self.session.exec_command.call_args[0][0])
        eq_(cmd, 'create /nodes/proxmox/openvz')
        ok_('-cpus 1' in options)
        ok_('-disk 4' in options)
        ok_('-hostname test' in options)
        ok_('-ip_address 10.0.100.222' in options)
        ok_('-memory 512' in options)
        ok_('-ostemplate local:vztmpl/debian-6-turnkey-core_12.0-1_i386.tar.gz' in options)
        ok_('-password secret' in options)
        ok_('-storage local' in options)
        ok_('-swap 512' in options)
        ok_('-vmid 800' in options)

        node = self.proxmox.nodes('proxmox1')
        node.openvz.post(vmid=900,
                         ostemplate='local:vztmpl/debian-7-turnkey-core_12.0-1_i386.tar.gz',
                         hostname='test1',
                         storage='local1',
                         memory=1024,
                         swap=1024,
                         cpus=2,
                         disk=8,
                         password='secret1',
                         ip_address='10.0.100.111')
        cmd, options = self._split_cmd(self.session.exec_command.call_args[0][0])
        eq_(cmd, 'create /nodes/proxmox1/openvz')
        ok_('-cpus 2' in options)
        ok_('-disk 8' in options)
        ok_('-hostname test1' in options)
        ok_('-ip_address 10.0.100.111' in options)
        ok_('-memory 1024' in options)
        ok_('-ostemplate local:vztmpl/debian-7-turnkey-core_12.0-1_i386.tar.gz' in options)
        ok_('-password secret1' in options)
        ok_('-storage local1' in options)
        ok_('-swap 1024' in options)
        ok_('-vmid 900' in options)

    def test_put(self):
        node = self.proxmox.nodes('proxmox')
        node.openvz(101).config.set(cpus=4, memory=1024, ip_address='10.0.100.100', onboot=True)
        cmd, options = self._split_cmd(self.session.exec_command.call_args[0][0])
        eq_(cmd, 'set /nodes/proxmox/openvz/101/config')
        ok_('-memory 1024' in options)
        ok_('-ip_address 10.0.100.100' in options)
        ok_('-onboot True' in options)
        ok_('-cpus 4' in options)

        node = self.proxmox.nodes('proxmox1')
        node.openvz('102').config.put(cpus=2, memory=512, ip_address='10.0.100.200', onboot=False)
        cmd, options = self._split_cmd(self.session.exec_command.call_args[0][0])
        eq_(cmd, 'set /nodes/proxmox1/openvz/102/config')
        ok_('-memory 512' in options)
        ok_('-ip_address 10.0.100.200' in options)
        ok_('-onboot False' in options)
        ok_('-cpus 2' in options)