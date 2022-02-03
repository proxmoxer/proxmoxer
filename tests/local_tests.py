import mock
from mock import patch
from nose.tools import assert_raises

from testfixtures import Replacer

from proxmoxer import ProxmoxAPI
from tests.base.base_suite import BaseSuite


def test_local_invalid_backend():
    with assert_raises(NotImplementedError):
        ProxmoxAPI(backend="local", service="PBS")


class TestLocalSuite(BaseSuite):
    def setup(self):
        self.proxmox = ProxmoxAPI(backend="local")

        self.Popen = mock.Mock()
        self.r = Replacer()
        self.r.replace('proxmoxer.backends.local.Popen', self.Popen)

        self._set_output(stdout="200 OK")

    def teardown(self):
        self.r.restore()

    def _get_called_cmd(self):
        return list(self.Popen.call_args.args[0])

    def _set_output(self, stdout='', stderr=''):
        self.Popen.return_value.communicate.return_value = (
            stdout.encode("utf-8"),
            stderr.encode("utf-8"),
        )
