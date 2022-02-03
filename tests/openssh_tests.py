__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"

from mock import patch
import shlex

from proxmoxer import ProxmoxAPI
from tests.base.base_suite import BaseSuite


class TestOpenSSHSuite(BaseSuite):
    # noinspection PyMethodOverriding
    @patch("openssh_wrapper.SSHConnection")
    def setup(self, _):
        self.proxmox = ProxmoxAPI("proxmox", user="root", backend="openssh", port=123)
        self.client = self.proxmox._store["session"].ssh_client
        self._set_output(stdout="200 OK")

    def _get_called_cmd(self):
        return shlex.split(self.client.run.call_args[0][0])

    def _set_output(self, stdout='', stderr=''):
        self.client.run.return_value.stdout = stdout
        self.client.run.return_value.stderr = stderr
