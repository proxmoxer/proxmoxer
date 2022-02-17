__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"

import io
import shlex

from mock import patch
from nose.tools import assert_raises, eq_

from proxmoxer import ProxmoxAPI
from tests.base.base_suite import CommandBaseSuite


@patch("paramiko.SSHClient")
def test_paramiko_connection(_):
    proxmox = ProxmoxAPI("proxmox", user="root", backend="ssh_paramiko", port=123)
    session = proxmox._store["session"]
    eq_(session.ssh_client.connect.call_args[0], ("proxmox",))
    eq_(
        session.ssh_client.connect.call_args[1],
        {
            "username": "root",
            "allow_agent": True,
            "key_filename": None,
            "look_for_keys": True,
            "timeout": 5,
            "password": None,
            "port": 123,
        },
    )


@patch("paramiko.SSHClient")
def test_paramiko_invalid_backend(_):
    with assert_raises(NotImplementedError):
        ProxmoxAPI("proxmox", user="root", backend="ssh_paramiko", port=123, service="PBS")


@patch("paramiko.SSHClient")
def test_paramiko_tokens(_):
    p = ProxmoxAPI("proxmox", user="root", backend="ssh_paramiko", port=123)
    eq_(p.get_tokens()[0], None)
    eq_(p.get_tokens()[1], None)


class TestParamikoSuite(CommandBaseSuite):

    # noinspection PyMethodOverriding
    @patch("paramiko.SSHClient")
    def setup(self, _):
        self.proxmox = ProxmoxAPI(
            "proxmox", user="root", backend="ssh_paramiko", port=123, sudo=self.sudo
        )
        self.client = self.proxmox._store["session"].ssh_client
        self.session = self.client.get_transport().open_session()
        self._set_output(stdout="200 OK")

    def _get_called_cmd(self):
        return shlex.split(self.session.exec_command.call_args[0][0])

    def _set_output(self, stdout="", stderr=""):
        self.session.makefile.return_value = io.BytesIO(stdout.encode("utf-8"))
        self.session.makefile_stderr.return_value = io.BytesIO(stderr.encode("utf-8"))


class TestParamikoSuiteWithSudo(TestParamikoSuite):
    def __init__(self):
        super(TestParamikoSuiteWithSudo, self).__init__(sudo=True)
