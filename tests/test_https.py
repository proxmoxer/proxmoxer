import logging
import re
import sys
import tempfile
from unittest import mock

import pytest
from requests import Request, Response

import proxmoxer as core
from proxmoxer.backends import https

from .api_mock import (  # pylint: disable=unused-import # noqa: F401
    PVERegistry,
    mock_pve,
)

# pylint: disable=no-self-use

MODULE_LOGGER_NAME = "proxmoxer.backends.https"


class TestHttpsBackend:
    """
    Tests for the proxmox.backends.https file.
    Only tests the Backend class for correct setting of
    variables and selection of auth class.
    Other classes are separately tested.
    """

    def test_init_no_auth(self):
        with pytest.raises(NotImplementedError) as exc_info:
            https.Backend("1.2.3.4:1234")

        assert str(exc_info.value) == "No valid authentication credentials were supplied"

    def test_init_ip4_separate_port(self):
        backend = https.Backend("1.2.3.4", port=1234, token_name="")
        exp_base_url = "https://1.2.3.4:1234/api2/json"

        assert backend.get_base_url() == exp_base_url

    def test_init_ip4_inline_port(self):
        backend = https.Backend("1.2.3.4:1234", token_name="")
        exp_base_url = "https://1.2.3.4:1234/api2/json"

        assert backend.get_base_url() == exp_base_url

    def test_init_ip6_separate_port(self):
        backend = https.Backend("2001:db8::1:2:3:4", port=1234, token_name="")
        exp_base_url = "https://[2001:db8::1:2:3:4]:1234/api2/json"

        assert backend.get_base_url() == exp_base_url

    def test_init_ip6_brackets_separate_port(self):
        backend = https.Backend("[2001:0db8::1:2:3:4]", port=1234, token_name="")
        exp_base_url = "https://[2001:0db8::1:2:3:4]:1234/api2/json"

        assert backend.get_base_url() == exp_base_url

    def test_init_ip6_inline_port(self):
        backend = https.Backend("[2001:db8::1:2:3:4]:1234", token_name="")
        exp_base_url = "https://[2001:db8::1:2:3:4]:1234/api2/json"

        assert backend.get_base_url() == exp_base_url

    def test_init_ip4_no_port(self):
        backend = https.Backend("1.2.3.4", token_name="")
        exp_base_url = "https://1.2.3.4:8006/api2/json"

        assert backend.get_base_url() == exp_base_url

    def test_init_path_prefix(self):
        backend = https.Backend("1.2.3.4:1234", path_prefix="path", token_name="")
        exp_base_url = "https://1.2.3.4:1234/path/api2/json"

        assert backend.get_base_url() == exp_base_url

    def test_init_token_pass(self):
        backend = https.Backend("1.2.3.4:1234", token_name="name")

        assert isinstance(backend.auth, https.ProxmoxHTTPApiTokenAuth)

    def test_init_token_not_supported(self, apply_none_service):
        with pytest.raises(NotImplementedError) as exc_info:
            https.Backend("1.2.3.4:1234", token_name="name", service="NONE")

        assert str(exc_info.value) == "NONE does not support API Token authentication"

    def test_init_password_not_supported(self, apply_none_service):
        with pytest.raises(NotImplementedError) as exc_info:
            https.Backend("1.2.3.4:1234", password="pass", service="NONE")

        assert str(exc_info.value) == "NONE does not support password authentication"

    def test_get_tokens_api_token(self):
        backend = https.Backend("1.2.3.4:1234", token_name="name")

        assert backend.get_tokens() == (None, None)

    def test_get_tokens_password(self, mock_pve):

        backend = https.Backend("1.2.3.4:1234", password="name")

        assert ("ticket", "CSRFPreventionToken") == backend.get_tokens()


class TestProxmoxHTTPAuthBase:
    """
    Tests the ProxmoxHTTPAuthBase class
    """

    base_url = PVERegistry.base_url

    def test_init_all_args(self):
        auth = https.ProxmoxHTTPAuthBase(timeout=1234, service="PMG", verify_ssl=True)

        assert auth.timeout == 1234
        assert auth.service == "PMG"
        assert auth.verify_ssl is True

    def test_call(self):
        auth = https.ProxmoxHTTPAuthBase()
        req = Request("HEAD", self.base_url + "/version").prepare()
        resp = auth(req)

        assert resp == req

    def test_get_cookies(self):
        auth = https.ProxmoxHTTPAuthBase()

        assert auth.get_cookies().get_dict() == {}


class TestProxmoxHTTPApiTokenAuth:
    """
    Tests the ProxmoxHTTPApiTokenAuth class
    """

    base_url = PVERegistry.base_url

    def test_init_all_args(self):
        auth = https.ProxmoxHTTPApiTokenAuth(
            "user", "name", "value", service="PMG", timeout=1234, verify_ssl=True
        )

        assert auth.username == "user"
        assert auth.token_name == "name"
        assert auth.token_value == "value"
        assert auth.service == "PMG"
        assert auth.timeout == 1234
        assert auth.verify_ssl is True

    def test_call_pve(self):
        auth = https.ProxmoxHTTPApiTokenAuth("user", "name", "value", service="PVE")
        req = Request("HEAD", self.base_url + "/version").prepare()
        resp = auth(req)

        assert resp.headers["Authorization"] == "PVEAPIToken=user!name=value"

    def test_call_pbs(self):
        auth = https.ProxmoxHTTPApiTokenAuth("user", "name", "value", service="PBS")
        req = Request("HEAD", self.base_url + "/version").prepare()
        resp = auth(req)

        assert resp.headers["Authorization"] == "PBSAPIToken=user!name:value"


class TestProxmoxHTTPAuth:
    """
    Tests the ProxmoxHTTPApiTokenAuth class
    """

    base_url = PVERegistry.base_url

    # pylint: disable=redefined-outer-name

    def test_init_all_args(self, mock_pve):
        auth = https.ProxmoxHTTPAuth(
            "otp",
            "password",
            otp="otp",
            base_url=self.base_url,
            service="PMG",
            timeout=1234,
            verify_ssl=True,
        )

        assert auth.username == "otp"
        assert auth.pve_auth_ticket == "ticket"
        assert auth.csrf_prevention_token == "CSRFPreventionToken"
        assert auth.service == "PMG"
        assert auth.timeout == 1234
        assert auth.verify_ssl is True

    def test_ticket_renewal(self, mock_pve):
        auth = https.ProxmoxHTTPAuth("user", "password", base_url=self.base_url)

        auth(Request("HEAD", self.base_url + "/version").prepare())

        # check starting auth tokens
        assert auth.pve_auth_ticket == "ticket"
        assert auth.csrf_prevention_token == "CSRFPreventionToken"

        auth.renew_age = 0  # force renewing ticket now
        auth(Request("GET", self.base_url + "/version").prepare())

        # check renewed auth tokens
        assert auth.pve_auth_ticket == "new_ticket"
        assert auth.csrf_prevention_token == "CSRFPreventionToken_2"

    def test_get_cookies(self, mock_pve):
        auth = https.ProxmoxHTTPAuth("user", "password", base_url=self.base_url, service="PVE")

        assert auth.get_cookies().get_dict() == {"PVEAuthCookie": "ticket"}

    def test_auth_failure(self, mock_pve):
        with pytest.raises(core.AuthenticationError) as exc_info:
            https.ProxmoxHTTPAuth("bad_auth", "", base_url=self.base_url)

        assert (
            str(exc_info.value)
            == f"Couldn't authenticate user: bad_auth to {self.base_url}/access/ticket"
        )

    def test_auth_otp(self, mock_pve):
        https.ProxmoxHTTPAuth(
            "otp", "password", base_url=self.base_url, otp="123456", service="PVE"
        )

    def test_auth_otp_missing(self, mock_pve):
        with pytest.raises(core.AuthenticationError) as exc_info:
            https.ProxmoxHTTPAuth("otp", "password", base_url=self.base_url, service="PVE")

        assert (
            str(exc_info.value)
            == "Couldn't authenticate user: missing Two Factor Authentication (TFA)"
        )


class TestProxmoxHttpSession:
    """
    Tests the ProxmoxHttpSession class
    """

    base_url = PVERegistry.base_url
    _session = https.Backend("1.2.3.4", token_name="").get_session()

    def test_request_basic(self, mock_pve):
        resp = self._session.request("GET", self.base_url + "/fake/echo")
        content = resp.json()

        assert content["method"] == "GET"
        assert content["url"] == self.base_url + "/fake/echo"
        assert content["body"] is None
        assert content["headers"]["accept"] == https.JsonSerializer().get_accept_types()

    def test_request_data(self, mock_pve):
        resp = self._session.request("GET", self.base_url + "/fake/echo", data={"key": "value"})
        content = resp.json()

        assert content["method"] == "GET"
        assert content["url"] == self.base_url + "/fake/echo"
        assert content["body"] == "key=value"
        assert content["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_request_command_list(self, mock_pve):
        resp = self._session.request(
            "GET", self.base_url + "/fake/echo", data={"command": ["echo", "hello", "world"]}
        )
        content = resp.json()

        assert content["method"] == "GET"
        assert content["url"] == self.base_url + "/fake/echo"
        assert content["body"] == "command=echo&command=hello&command=world"
        assert content["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_request_command_string(self, mock_pve):
        resp = self._session.request(
            "GET", self.base_url + "/fake/echo", data={"command": "echo hello world"}
        )
        content = resp.json()

        assert content["method"] == "GET"
        assert content["url"] == self.base_url + "/fake/echo"
        assert content["body"] == "command=echo&command=hello&command=world"
        assert content["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_request_file(self, mock_pve):
        size = 10
        content = {}
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(0)
            resp = self._session.request("GET", self.base_url + "/fake/echo", data={"iso": f_obj})
            content = resp.json()

        # decode multipart file
        body_regex = f'--([0-9a-f]*)\r\nContent-Disposition: form-data; name="iso"\r\n\r\na{{{size}}}\r\n--\\1--\r\n'
        m = re.match(body_regex, content["body"])

        assert content["method"] == "GET"
        assert content["url"] == self.base_url + "/fake/echo"
        assert m is not None  # content matches multipart for the created file
        assert content["headers"]["Content-Type"] == "multipart/form-data; boundary=" + m[1]

    def test_request_streaming(self, toolbelt_on_off, caplog, mock_pve):
        caplog.set_level(logging.INFO, logger=MODULE_LOGGER_NAME)

        size = https.STREAMING_SIZE_THRESHOLD + 1
        content = {}
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(0)
            resp = self._session.request("GET", self.base_url + "/fake/echo", data={"iso": f_obj})
            content = resp.json()

        # decode multipart file
        body_regex = f'--([0-9a-f]*)\r\nContent-Disposition: form-data; name="iso"\r\n\r\na{{{size}}}\r\n--\\1--\r\n'
        m = re.match(body_regex, content["body"])

        assert content["method"] == "GET"
        assert content["url"] == self.base_url + "/fake/echo"
        assert m is not None  # content matches multipart for the created file
        assert content["headers"]["Content-Type"] == "multipart/form-data; boundary=" + m[1]

        if not toolbelt_on_off:
            assert caplog.record_tuples == [
                (
                    MODULE_LOGGER_NAME,
                    logging.INFO,
                    "Installing 'requests_toolbelt' will decrease memory used during upload",
                )
            ]

    def test_request_large_file(self, shrink_thresholds, toolbelt_on_off, caplog, mock_pve):

        size = https.SSL_OVERFLOW_THRESHOLD + 1
        content = {}
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(0)

            if toolbelt_on_off:
                resp = self._session.request(
                    "GET", self.base_url + "/fake/echo", data={"iso": f_obj}
                )
                content = resp.json()

                # decode multipart file
                body_regex = f'--([0-9a-f]*)\r\nContent-Disposition: form-data; name="iso"\r\n\r\na{{{size}}}\r\n--\\1--\r\n'
                m = re.match(body_regex, content["body"])

                assert content["method"] == "GET"
                assert content["url"] == self.base_url + "/fake/echo"
                assert m is not None  # content matches multipart for the created file
                assert content["headers"]["Content-Type"] == "multipart/form-data; boundary=" + m[1]

            else:
                # forcing an ImportError
                with pytest.raises(OverflowError) as exc_info:
                    resp = self._session.request(
                        "GET", self.base_url + "/fake/echo", data={"iso": f_obj}
                    )

                assert str(exc_info.value) == "Unable to upload a payload larger than 2 GiB"
                assert caplog.record_tuples == [
                    (
                        MODULE_LOGGER_NAME,
                        logging.WARNING,
                        "Install 'requests_toolbelt' to add support for files larger than 2GiB",
                    )
                ]

    def test_request_filename(self, mock_pve):
        resp = self._session.request(
            "GET",
            self.base_url + "/fake/echo",
            files={"file1": "content"},
            serializer=https.JsonSerializer,
        )
        content = resp.json()

        # decode multipart file
        body_regex = '--([0-9a-f]*)\r\nContent-Disposition: form-data; name="file1"; filename="file1"\r\n\r\ncontent\r\n--\\1--\r\n'
        m = re.match(body_regex, content["body"])

        assert content["method"] == "GET"
        assert content["url"] == self.base_url + "/fake/echo"
        assert m is not None  # content matches multipart for the created file
        assert content["headers"]["Content-Type"] == "multipart/form-data; boundary=" + m[1]


# pylint: disable=protected-access
class TestJsonSerializer:
    _serializer = https.JsonSerializer()

    def test_get_accept_types(self):
        ctypes = "application/json, application/x-javascript, text/javascript, text/x-javascript, text/x-json"
        assert ctypes == self._serializer.get_accept_types()

    def test_loads_pass(self):
        input_str = '{"data": {"key1": "value1", "key2": "value2"}, "errors": {}}'
        exp_output = {"key1": "value1", "key2": "value2"}

        response = Response()
        response._content = input_str.encode("utf-8")

        act_output = self._serializer.loads(response)

        assert act_output == exp_output

    def test_loads_not_json(self):
        input_str = "There was an error with the request"
        exp_output = {"errors": b"There was an error with the request"}

        response = Response()
        response._content = input_str.encode("utf-8")

        act_output = self._serializer.loads(response)

        assert act_output == exp_output

    def test_loads_not_unicode(self):
        input_str = '{"data": {"key1": "value1", "key2": "value2"}, "errors": {}}\x80'
        exp_output = {"errors": input_str.encode("utf-8")}

        response = Response()
        response._content = input_str.encode("utf-8")

        act_output = self._serializer.loads(response)

        assert act_output == exp_output

    def test_loads_errors_pass(self):
        input_str = (
            '{"data": {}, "errors": ["missing required param 1", "missing required param 2"]}'
        )
        exp_output = ["missing required param 1", "missing required param 2"]

        response = Response()
        response._content = input_str.encode("utf-8")

        act_output = self._serializer.loads_errors(response)

        assert act_output == exp_output

    def test_loads_errors_not_json(self):
        input_str = (
            '{"data": {} "errors": ["missing required param 1", "missing required param 2"]}'
        )
        exp_output = {
            "errors": b'{"data": {} "errors": ["missing required param 1", "missing required param 2"]}'
        }

        response = Response()
        response._content = input_str.encode("utf-8")

        act_output = self._serializer.loads_errors(response)

        assert act_output == exp_output

    def test_loads_errors_not_unicode(self):
        input_str = (
            '{"data": {}, "errors": ["missing required param 1", "missing required param 2"]}\x80'
        )
        exp_output = {"errors": input_str.encode("utf-8")}

        response = Response()
        response._content = input_str.encode("utf-8")

        act_output = self._serializer.loads_errors(response)

        assert act_output == exp_output


@pytest.fixture(params=(False, True))
def toolbelt_on_off(request, monkeypatch):
    """
    runs test twice, once with importing of 'requests_toolbelt' to be allowed
    and one with it disabled. Returns True if module is available, False if blocked.
    """
    if not request.param:
        # ran once with requests_toolbelt available and once with it removed
        monkeypatch.setitem(sys.modules, "requests_toolbelt", None)
    return request.param


@pytest.fixture
def shrink_thresholds():
    with mock.patch("proxmoxer.backends.https.STREAMING_SIZE_THRESHOLD", 100), mock.patch(
        "proxmoxer.backends.https.SSL_OVERFLOW_THRESHOLD", 1000
    ):
        yield


@pytest.fixture
def apply_none_service():
    serv = {
        "NONE": {
            "supported_backends": [],
            "supported_https_auths": [],
            "default_port": 1234,
        }
    }

    with mock.patch("proxmoxer.core.SERVICES", serv), mock.patch(
        "proxmoxer.backends.https.SERVICES", serv
    ):
        yield
