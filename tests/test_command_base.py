import tempfile
from unittest import mock

import pytest

from proxmoxer.backends import command_base

from .api_mock import PVERegistry

# pylint: disable=no-self-use


class TestResponse:
    def test_init_all_args(self):
        resp = command_base.Response(b"content", 200)

        assert resp.content == b"content"
        assert resp.text == "b'content'"
        assert resp.status_code == 200
        assert resp.headers == {"content-type": "application/json"}
        assert str(resp) == "Response (200) b'content'"


class TestCommandBaseSession:
    base_url = PVERegistry.base_url
    _session = command_base.CommandBaseSession()

    def test_init_all_args(self):
        sess = command_base.CommandBaseSession(service="SERVICE", timeout=10, sudo=True)

        assert sess.service == "service"
        assert sess.timeout == 10
        assert sess.sudo is True

    def test_exec(self):
        with pytest.raises(NotImplementedError):
            self._session._exec("command")

    def test_upload_file_obj(self):
        with pytest.raises(NotImplementedError), tempfile.TemporaryFile("w+b") as f_obj:
            self._session.upload_file_obj(f_obj, "/tmp/file.iso")

    def test_request_basic(self, mock_exec):
        resp = self._session.request("GET", self.base_url + "/fake/echo")

        assert resp.status_code == 200
        assert resp.content == [
            "pvesh",
            "get",
            self.base_url + "/fake/echo",
            "--output-format",
            "json",
        ]

    def test_request_error(self, mock_exec_err):
        resp = self._session.request(
            "GET", self.base_url + "/fake/echo", data={"thing": "403 Unauthorized"}
        )

        assert resp.status_code == 403
        assert (
            resp.content
            == "pvesh\nget\nhttps://1.2.3.4:1234/api2/json/fake/echo\n-thing\n403 Unauthorized\n--output-format\njson"
        )

    def test_request_error_generic(self, mock_exec_err):
        resp = self._session.request("GET", self.base_url + "/fake/echo", data={"thing": "failure"})

        assert resp.status_code == 500
        assert (
            resp.content
            == "pvesh\nget\nhttps://1.2.3.4:1234/api2/json/fake/echo\n-thing\nfailure\n--output-format\njson"
        )

    def test_request_sudo(self, mock_exec):
        resp = command_base.CommandBaseSession(sudo=True).request(
            "GET", self.base_url + "/fake/echo"
        )

        assert resp.status_code == 200
        assert resp.content == [
            "sudo",
            "pvesh",
            "get",
            self.base_url + "/fake/echo",
            "--output-format",
            "json",
        ]

    def test_request_data(self, mock_exec):
        resp = self._session.request("GET", self.base_url + "/fake/echo", data={"key": "value"})

        assert resp.status_code == 200
        assert resp.content == [
            "pvesh",
            "get",
            self.base_url + "/fake/echo",
            "-key",
            "value",
            "--output-format",
            "json",
        ]

    def test_request_qemu_exec(self, mock_exec):
        resp = self._session.request(
            "POST",
            self.base_url + "/node/node1/qemu/100/agent/exec",
            data={"command": "echo 'hello world'"},
        )

        assert resp.status_code == 200
        assert resp.content == [
            "pvesh",
            "create",
            self.base_url + "/node/node1/qemu/100/agent/exec",
            "-command",
            "echo",
            "-command",
            "hello world",
            "--output-format",
            "json",
        ]

    def test_request_qemu_exec_list(self, mock_exec):
        resp = self._session.request(
            "POST",
            self.base_url + "/node/node1/qemu/100/agent/exec",
            data={"command": ["echo", "hello world"]},
        )

        assert resp.status_code == 200
        assert resp.content == [
            "pvesh",
            "create",
            self.base_url + "/node/node1/qemu/100/agent/exec",
            "-command",
            "echo",
            "-command",
            "hello world",
            "--output-format",
            "json",
        ]

    def test_request_upload(self, mock_exec, mock_upload_file_obj):
        with tempfile.NamedTemporaryFile("w+b") as f_obj:
            resp = self._session.request(
                "POST",
                self.base_url + "/node/node1/storage/local/upload",
                data={"content": "iso", "filename": f_obj},
            )

            assert resp.status_code == 200
            assert resp.content == [
                "pvesh",
                "create",
                self.base_url + "/node/node1/storage/local/upload",
                "-content",
                "iso",
                "-filename",
                str(f_obj.name),
                "-tmpfilename",
                "/tmp/tmpasdfasdf",
                "--output-format",
                "json",
            ]


class TestJsonSimpleSerializer:
    _serializer = command_base.JsonSimpleSerializer()

    def test_loads_pass(self):
        input_str = '{"key1": "value1", "key2": "value2"}'
        exp_output = {"key1": "value1", "key2": "value2"}

        response = command_base.Response(input_str.encode("utf-8"), 200)

        act_output = self._serializer.loads(response)

        assert act_output == exp_output

    def test_loads_not_json(self):
        input_str = "There was an error with the request"
        exp_output = {"errors": b"There was an error with the request"}

        response = command_base.Response(input_str.encode("utf-8"), 200)

        act_output = self._serializer.loads(response)

        assert act_output == exp_output

    def test_loads_not_unicode(self):
        input_str = '{"data": {"key1": "value1", "key2": "value2"}, "errors": {}}\x80'
        exp_output = {"errors": input_str.encode("utf-8")}

        response = command_base.Response(input_str.encode("utf-8"), 200)

        act_output = self._serializer.loads(response)

        assert act_output == exp_output


class TestCommandBaseBackend:
    backend = command_base.CommandBaseBackend()
    sess = command_base.CommandBaseSession()

    backend.session = sess

    def test_get_session(self):
        assert self.backend.get_session() == self.sess

    def test_get_base_url(self):
        assert self.backend.get_base_url() == ""

    def test_get_serializer(self):
        assert isinstance(self.backend.get_serializer(), command_base.JsonSimpleSerializer)


@classmethod
def _exec_echo(_, cmd):
    # if getting a tmpfile on the remote, return fake tmpfile
    if cmd == [
        "python3",
        "-c",
        "import tempfile; import sys; tf = tempfile.NamedTemporaryFile(); sys.stdout.write(tf.name)",
    ]:
        return b"/tmp/tmpasdfasdf", None
    return cmd, None


@classmethod
def _exec_err(_, cmd):
    print("\n".join(cmd))
    return None, "\n".join(cmd)


@classmethod
def upload_file_obj_echo(_, file_obj, remote_path):
    return file_obj, remote_path


@pytest.fixture
def mock_upload_file_obj():
    with mock.patch.object(
        command_base.CommandBaseSession, "upload_file_obj", upload_file_obj_echo
    ):
        yield


@pytest.fixture
def mock_exec():
    with mock.patch.object(command_base.CommandBaseSession, "_exec", _exec_echo):
        yield


@pytest.fixture
def mock_exec_err():
    with mock.patch.object(command_base.CommandBaseSession, "_exec", _exec_err):
        yield
