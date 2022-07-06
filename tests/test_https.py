import pytest
from requests import Response

import proxmoxer.backends.https as https


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

    def test_init_token_pass(self):
        backend = https.Backend("1.2.3.4:1234", token_name="name")

        assert isinstance(backend.auth, https.ProxmoxHTTPApiTokenAuth)

    def test_init_token_not_supported(self):
        with pytest.raises(NotImplementedError) as exc_info:
            https.Backend("1.2.3.4:1234", token_name="name", service="NONE")

        assert str(exc_info.value) == "NONE does not support API Token authentication"

    def test_init_password_not_supported(self):
        with pytest.raises(NotImplementedError) as exc_info:
            https.Backend("1.2.3.4:1234", password="pass", service="NONE")

        assert str(exc_info.value) == "NONE does not support password authentication"

    def test_get_tokens_api_token(self):
        backend = https.Backend("1.2.3.4:1234", token_name="name")

        assert backend.get_tokens() == (None, None)


class TestProxmoxHTTPApiTokenAuth:
    """
    Tests the ProxmoxHTTPApiTokenAuth class
    """

    def test_init_all_args(self):
        auth = https.ProxmoxHTTPApiTokenAuth("user", "name", "value", "PMG")

        assert auth.username == "user"
        assert auth.token_name == "name"
        assert auth.token_value == "value"
        assert auth.service == "PMG"
        # TODO jhollowe update when HTTPS upgrade code gets merged


class TestProxmoxHttpSession:
    _session = https.Backend("1.2.3.4", token_name="").get_session()

    def test_request_basic(self):
        pass


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


class MockRequest:
    pass
