import tempfile
from unittest import mock

import openssh_wrapper
import pytest

from proxmoxer.backends import openssh

# pylint: disable=no-self-use


class TestOpenSSHBackend:
    def test_init(self):
        back = openssh.Backend("host", "user")

        assert isinstance(back.session, openssh.OpenSSHSession)
        assert back.session.host == "host"
        assert back.session.user == "user"


class TestOpenSSHSession:
    _session = openssh.OpenSSHSession("host", "user")

    def test_init_all_args(self):
        with tempfile.NamedTemporaryFile("r") as conf_obj, tempfile.NamedTemporaryFile(
            "r"
        ) as ident_obj:
            sess = openssh.OpenSSHSession(
                "host",
                "user",
                config_file=conf_obj.name,
                port=123,
                identity_file=ident_obj.name,
                forward_ssh_agent=True,
            )

            assert sess.host == "host"
            assert sess.user == "user"
            assert sess.config_file == conf_obj.name
            assert sess.port == 123
            assert sess.identity_file == ident_obj.name
            assert sess.forward_ssh_agent is True

    def test_exec(self, mock_session):
        cmd = [
            "echo",
            "hello",
            "world",
        ]

        stdout, stderr = mock_session._exec(cmd)

        assert stdout == "stdout content"
        assert stderr == "stderr content"
        mock_session.ssh_client.run.assert_called_once_with(
            "echo hello world",
            forward_ssh_agent=True,
        )

    def test_upload_file_obj(self, mock_session):
        with tempfile.NamedTemporaryFile("r") as f_obj:
            mock_session.upload_file_obj(f_obj, "/tmp/file")

            mock_session.ssh_client.scp.assert_called_once_with(
                (f_obj,),
                target="/tmp/file",
            )


@pytest.fixture
def mock_session():
    with mock.patch("proxmoxer.backends.openssh.OpenSSHSession._connect", _get_mock_ssh_conn):
        yield openssh.OpenSSHSession("host", "user", forward_ssh_agent=True)


def _get_mock_ssh_conn(_):
    ssh_conn = mock.Mock(spec=openssh_wrapper.SSHConnection)

    ssh_conn.run = mock.Mock(
        # spec=openssh_wrapper.SSHConnection.run,
        return_value=mock.Mock(stdout="stdout content", stderr="stderr content"),
    )

    ssh_conn.scp = mock.Mock()

    return ssh_conn
