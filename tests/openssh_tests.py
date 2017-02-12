__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2017'
__licence__ = 'MIT'

from mock import patch
from proxmoxer import ProxmoxAPI
from tests.base.base_ssh_suite import BaseSSHSuite


class TestOpenSSHSuite(BaseSSHSuite):
    proxmox = None
    client = None

    # noinspection PyMethodOverriding
    @patch('openssh_wrapper.SSHConnection')
    def setUp(self, _):
        self.proxmox = ProxmoxAPI('proxmox', user='root', backend='openssh', port=123)
        self.client = self.proxmox._store['session'].ssh_client
        self._set_stderr('200 OK')
        self._set_stdout('')

    def _get_called_cmd(self):
        return self.client.run.call_args[0][0]

    def _set_stdout(self, stdout):
        self.client.run.return_value.stdout = stdout

    def _set_stderr(self, stderr):
        self.client.run.return_value.stderr = stderr
