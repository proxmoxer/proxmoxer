__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2017'
__licence__ = 'MIT'

import io
from mock import patch
from nose.tools import assert_raises
from proxmoxer import ProxmoxAPI
from tests.base.base_ssh_suite import BaseSSHSuite


@patch('subprocess.Popen')
def test_cli_invalid_backend(_):
    with assert_raises(TypeError):
        ProxmoxAPI()


class TestOpenCliSuite(BaseSSHSuite):
    proxmox = None
    client = None

    # noinspection PyMethodOverriding
    @patch('subprocess.Popen')
    def setUp(self, _):
        self.proxmox = ProxmoxAPI(backend='cli')
        self.client = self.proxmox._store['session'].ssh_client
        self._set_stderr('200 OK')
        self._set_stdout('')

    def _get_called_cmd(self):
        return self.session.exec_command.call_args[0][0]

    def _set_stdout(self, stdout):
        self.session.makefile.return_value = io.BytesIO(stdout.encode('utf-8'))

    def _set_stderr(self, stderr):
        self.session.makefile_stderr.return_value = io.BytesIO(stderr.encode('utf-8'))


class TestOpenCliSuiteWithSudo(BaseSSHSuite):
    proxmox = None
    client = None

    # noinspection PyMethodOverriding
    @patch('subprocess.Popen')
    def setUp(self, _):
        super(TestOpenCliSuiteWithSudo, self).__init__(sudo=True)
        self.proxmox = ProxmoxAPI(backend='cli', sudo=True)
        self.client = self.proxmox._store['session'].ssh_client
        self._set_stderr('200 OK')
        self._set_stdout('')

    def _get_called_cmd(self):
        return self.session.exec_command.call_args[0][0]

    def _set_stdout(self, stdout):
        self.session.makefile.return_value = io.BytesIO(stdout.encode('utf-8'))

    def _set_stderr(self, stderr):
        self.session.makefile_stderr.return_value = io.BytesIO(stderr.encode('utf-8'))

