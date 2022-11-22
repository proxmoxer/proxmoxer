import os.path
import tempfile
from unittest import mock

import pytest

from proxmoxer.backends import ssh_paramiko

# pylint: disable=no-self-use


class TestParamikoBackend:
    def test_init(self, mock_connect):
        back = ssh_paramiko.Backend("host", "user")

        assert isinstance(back.session, ssh_paramiko.SshParamikoSession)
        assert back.session.host == "host"
        assert back.session.user == "user"


class TestSshParamikoSession:
    def test_init_all_args(self, mock_connect):
        sess = ssh_paramiko.SshParamikoSession(
            "host", "user", password="password", private_key_file="/tmp/key_file", port=1234
        )

        assert sess.host == "host"
        assert sess.user == "user"
        assert sess.password == "password"
        assert sess.private_key_file == "/tmp/key_file"
        assert sess.port == 1234
        assert sess.ssh_client == mock_connect()

    def test_connect_basic(self, mock_ssh_client):
        import paramiko

        sess = ssh_paramiko.SshParamikoSession("host", "user", password="password", port=1234)

        sess.ssh_client.connect.assert_called_once_with(
            "host",
            username="user",
            allow_agent=False,
            look_for_keys=True,
            key_filename=None,
            password="password",
            timeout=5,
            port=1234,
        )
        policy_call_args, _ = sess.ssh_client.set_missing_host_key_policy.call_args_list[0]
        assert isinstance(policy_call_args[0], paramiko.AutoAddPolicy)

    def test_connect_key_file(self, mock_ssh_client):
        import paramiko

        sess = ssh_paramiko.SshParamikoSession(
            "host", "user", password="password", private_key_file="/tmp/key_file", port=1234
        )

        sess.ssh_client.connect.assert_called_once_with(
            "host",
            username="user",
            allow_agent=False,
            look_for_keys=True,
            key_filename="/tmp/key_file",
            password="password",
            timeout=5,
            port=1234,
        )
        policy_call_args, _ = sess.ssh_client.set_missing_host_key_policy.call_args_list[0]
        assert isinstance(policy_call_args[0], paramiko.AutoAddPolicy)

    def test_connect_key_file_user(self, mock_ssh_client):
        import paramiko

        sess = ssh_paramiko.SshParamikoSession(
            "host", "user", password="password", private_key_file="~/key_file", port=1234
        )

        sess.ssh_client.connect.assert_called_once_with(
            "host",
            username="user",
            allow_agent=False,
            look_for_keys=True,
            key_filename=os.path.expanduser("~") + "/key_file",
            password="password",
            timeout=5,
            port=1234,
        )
        policy_call_args, _ = sess.ssh_client.set_missing_host_key_policy.call_args_list[0]
        assert isinstance(policy_call_args[0], paramiko.AutoAddPolicy)

    def test_exec(self, mock_ssh_client):
        mock_client, mock_session, _ = mock_ssh_client

        sess = ssh_paramiko.SshParamikoSession("host", "user")
        sess.ssh_client = mock_client

        stdout, stderr = sess._exec(["echo", "hello", "world"])

        assert stdout == "stdout contents"
        assert stderr == "stderr contents"
        mock_session.exec_command.assert_called_once_with("echo hello world")

    def test_upload_file_obj(self, mock_ssh_client):
        mock_client, _, mock_sftp = mock_ssh_client

        sess = ssh_paramiko.SshParamikoSession("host", "user")
        sess.ssh_client = mock_client

        with tempfile.NamedTemporaryFile("r") as f_obj:
            sess.upload_file_obj(f_obj, "/tmp/file")

            mock_sftp.putfo.assert_called_once_with(f_obj, "/tmp/file")

        mock_sftp.close.assert_called_once_with()


@pytest.fixture
def mock_connect():
    m = mock.Mock(spec=ssh_paramiko.SshParamikoSession._connect)
    with mock.patch(
        "proxmoxer.backends.ssh_paramiko.SshParamikoSession._connect",
        m,
    ):
        yield m


@pytest.fixture
def mock_ssh_client():
    # pylint: disable=import-outside-toplevel
    from paramiko import SFTPClient, SSHClient, Transport, channel

    mock_client = mock.Mock(spec=SSHClient)
    mock_transport = mock.Mock(spec=Transport)
    mock_channel = mock.Mock(spec=channel.Channel)
    mock_sftp = mock.Mock(spec=SFTPClient)

    # mock the return streams from the SSH connection
    mock_stdout = mock.Mock(spec=channel.ChannelFile)
    mock_stderr = mock.Mock(spec=channel.ChannelStderrFile)
    mock_stdout.read.return_value = b"stdout contents"
    mock_stderr.read.return_value = b"stderr contents"
    mock_channel.makefile.return_value = mock_stdout
    mock_channel.makefile_stderr.return_value = mock_stderr

    mock_transport.open_session.return_value = mock_channel
    mock_client.get_transport.return_value = mock_transport
    mock_client.open_sftp.return_value = mock_sftp

    with mock.patch("paramiko.SSHClient", mock_client):
        yield (mock_client, mock_channel, mock_sftp)
