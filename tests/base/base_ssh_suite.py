__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2016'
__licence__ = 'MIT'

from itertools import islice

try:
    import itertools.izip as zip
except ImportError:
    pass

from nose.tools import eq_, ok_


class BaseSSHSuite():
    proxmox = None
    client = None
    session = None

    def _split_cmd(self, cmd):
        splitted = cmd.split()
        eq_(splitted[0], 'pvesh')
        options_set = set((' '.join((k, v)) for k, v in
                           zip(islice(splitted, 3, None, 2), islice(splitted, 4, None, 2))))
        return ' '.join(splitted[1:3]), options_set

    def _get_called_cmd(self):
        raise NotImplementedError()

    def _set_stdout(self, stdout):
        raise NotImplementedError()

    def _set_stderr(self, stderr):
        raise NotImplementedError()

    def test_get(self):
        self._set_stdout("""
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
            ]""")
        result = self.proxmox.nodes('proxmox').storage('local').get()
        eq_(self._get_called_cmd(), 'pvesh get /nodes/proxmox/storage/local')
        eq_(result[0]['subdir'], 'status')
        eq_(result[1]['subdir'], 'content')
        eq_(result[2]['subdir'], 'upload')
        eq_(result[3]['subdir'], 'rrd')
        eq_(result[4]['subdir'], 'rrddata')

    def test_delete(self):
        self.proxmox.nodes('proxmox').openvz(100).delete()
        eq_(self._get_called_cmd(), 'pvesh delete /nodes/proxmox/openvz/100')
        self.proxmox.nodes('proxmox').openvz('101').delete()
        eq_(self._get_called_cmd(), 'pvesh delete /nodes/proxmox/openvz/101')
        self.proxmox.nodes('proxmox').openvz.delete('102')
        eq_(self._get_called_cmd(), 'pvesh delete /nodes/proxmox/openvz/102')

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
        cmd, options = self._split_cmd(self._get_called_cmd())
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
        cmd, options = self._split_cmd(self._get_called_cmd())
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
        cmd, options = self._split_cmd(self._get_called_cmd())
        eq_(cmd, 'set /nodes/proxmox/openvz/101/config')
        ok_('-memory 1024' in options)
        ok_('-ip_address 10.0.100.100' in options)
        ok_('-onboot True' in options)
        ok_('-cpus 4' in options)

        node = self.proxmox.nodes('proxmox1')
        node.openvz('102').config.put(cpus=2, memory=512, ip_address='10.0.100.200', onboot=False)
        cmd, options = self._split_cmd(self._get_called_cmd())
        eq_(cmd, 'set /nodes/proxmox1/openvz/102/config')
        ok_('-memory 512' in options)
        ok_('-ip_address 10.0.100.200' in options)
        ok_('-onboot False' in options)
        ok_('-cpus 2' in options)
