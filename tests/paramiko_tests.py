__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2017'
__licence__ = 'MIT'

import io
from mock import patch
from nose.tools import eq_
from proxmoxer import ProxmoxAPI
from .base.base_ssh_suite import BaseSSHSuite


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


class TestParamikoSuite(BaseSSHSuite):

    # noinspection PyMethodOverriding
    @patch('paramiko.SSHClient')
    def setUp(self, _):
        self.proxmox = ProxmoxAPI('proxmox', user='root', backend='ssh_paramiko', port=123)
        self.client = self.proxmox._store['session'].ssh_client
        self.session = self.client.get_transport().open_session()
        self._set_stderr('200 OK')
        self._set_stdout('')

    def _get_called_cmd(self):
        return self.session.exec_command.call_args[0][0]

    def _set_stdout(self, stdout):
        self.session.makefile.return_value = io.BytesIO(stdout.encode('utf-8'))

    def _set_stderr(self, stderr):
        self.session.makefile_stderr.return_value = io.BytesIO(stderr.encode('utf-8'))


class TestParamikoSuiteWithSudo(BaseSSHSuite):

    # noinspection PyMethodOverriding
    @patch('paramiko.SSHClient')
    def setUp(self, _):
        super(TestParamikoSuiteWithSudo, self).__init__(sudo=True)
        self.proxmox = ProxmoxAPI('proxmox', user='root', backend='ssh_paramiko', port=123, sudo=True)
        self.client = self.proxmox._store['session'].ssh_client
        self.session = self.client.get_transport().open_session()
        self._set_stderr('200 OK')
        self._set_stdout('')

    def _get_called_cmd(self):
        return self.session.exec_command.call_args[0][0]

    def _set_stdout(self, stdout):
        self.session.makefile.return_value = io.BytesIO(stdout.encode('utf-8'))

    def _set_stderr(self, stderr):
        self.session.makefile_stderr.return_value = io.BytesIO(stderr.encode('utf-8'))
