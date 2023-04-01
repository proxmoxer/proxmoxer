__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2022"
__license__ = "MIT"

import logging
import sys
from importlib import reload

import pytest


def test_missing_requests(requests_off, caplog):
    with pytest.raises(SystemExit) as exit_exp:
        import proxmoxer.backends.https as test_https

        # force re-importing of the module with `requests` gone so the validation is triggered
        reload(test_https)

    assert exit_exp.value.code == 1
    assert caplog.record_tuples == [
        (
            "proxmoxer.backends.https",
            logging.ERROR,
            "Chosen backend requires 'requests' module\n",
        )
    ]


def test_missing_requests_tools_files(requests_off, caplog):
    with pytest.raises(SystemExit) as exit_exp:
        import proxmoxer.tools.files as test_files

        # force re-importing of the module with `requests` gone so the validation is triggered
        reload(test_files)

    assert exit_exp.value.code == 1
    assert caplog.record_tuples == [
        (
            "proxmoxer.tools.files",
            logging.ERROR,
            "Files tools requires 'requests' module\n",
        )
    ]


def test_missing_openssh_wrapper(openssh_off, caplog):
    with pytest.raises(SystemExit) as exit_exp:
        import proxmoxer.backends.openssh as test_openssh

        # force re-importing of the module with `openssh_wrapper` gone so the validation is triggered
        reload(test_openssh)

    assert exit_exp.value.code == 1
    assert caplog.record_tuples == [
        (
            "proxmoxer.backends.openssh",
            logging.ERROR,
            "Chosen backend requires 'openssh_wrapper' module\n",
        )
    ]


def test_missing_paramiko_off(paramiko_off, caplog):
    with pytest.raises(SystemExit) as exit_exp:
        import proxmoxer.backends.ssh_paramiko as ssh_paramiko

        # force re-importing of the module with `ssh_paramiko` gone so the validation is triggered
        reload(ssh_paramiko)

    assert exit_exp.value.code == 1
    assert caplog.record_tuples == [
        (
            "proxmoxer.backends.ssh_paramiko",
            logging.ERROR,
            "Chosen backend requires 'paramiko' module\n",
        )
    ]


class TestCommandBase:
    def test_join_empty(self, shlex_join_on_off):
        from proxmoxer.backends import command_base

        reload(command_base)

        arr = []

        assert command_base.shell_join(arr) == ""

    def test_join_single(self, shlex_join_on_off):
        from proxmoxer.backends import command_base

        reload(command_base)

        arr = ["echo"]

        assert command_base.shell_join(arr) == "echo"

    def test_join_multiple(self, shlex_join_on_off):
        from proxmoxer.backends import command_base

        reload(command_base)

        arr = ["echo", "test"]

        assert command_base.shell_join(arr) == "echo test"

    def test_join_complex(self, shlex_join_on_off):
        from proxmoxer.backends import command_base

        reload(command_base)

        arr = ["echo", 'hello "world"']

        assert command_base.shell_join(arr) == "echo 'hello \"world\"'"


@pytest.fixture()
def requests_off(monkeypatch):
    return monkeypatch.setitem(sys.modules, "requests", None)


@pytest.fixture()
def openssh_off(monkeypatch):
    return monkeypatch.setitem(sys.modules, "openssh_wrapper", None)


@pytest.fixture()
def paramiko_off(monkeypatch):
    return monkeypatch.setitem(sys.modules, "paramiko", None)


@pytest.fixture(params=(False, True))
def shlex_join_on_off(request, monkeypatch):
    """
    runs test twice, once with importing of 'shlex.join' to be allowed
    and one with it disabled. Returns True if module is available, False if blocked.
    """

    if not request.param:
        # ran once with shlex available and once with it removed
        if getattr(sys.modules["shlex"], "join", None):
            monkeypatch.delattr(sys.modules["shlex"], "join")
        # else join already does not exist (py < 3.8)
    return request.param
