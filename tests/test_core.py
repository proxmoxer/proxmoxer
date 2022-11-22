import logging
from unittest import mock

import pytest

from proxmoxer import core
from proxmoxer.backends import https
from proxmoxer.backends.command_base import JsonSimpleSerializer, Response

from .api_mock import (  # pylint: disable=unused-import # noqa: F401
    PVERegistry,
    mock_pve,
)

# pylint: disable=no-self-use,protected-access

MODULE_LOGGER_NAME = "proxmoxer.core"


class TestResourceException:
    def test_init_none(self):
        e = core.ResourceException(None, None, None)

        assert e.status_code is None
        assert e.status_message is None
        assert e.content is None
        assert e.errors is None
        assert str(e) == "None None: None"

    def test_init_basic(self):
        e = core.ResourceException(500, "Internal Error", "Unable to do the thing")

        assert e.status_code == 500
        assert e.status_message == "Internal Error"
        assert e.content == "Unable to do the thing"
        assert e.errors is None
        assert str(e) == "500 Internal Error: Unable to do the thing"

    def test_init_error(self):
        e = core.ResourceException(
            500, "Internal Error", "Unable to do the thing", "functionality not found"
        )

        assert e.status_code == 500
        assert e.status_message == "Internal Error"
        assert e.content == "Unable to do the thing"
        assert e.errors == "functionality not found"
        assert str(e) == "500 Internal Error: Unable to do the thing - functionality not found"


class TestProxmoxResource:
    obj = core.ProxmoxResource()
    base_url = "http://example.com/"

    def test_url_join_empty_base(self):
        assert "/" == self.obj.url_join("", "")

    def test_url_join_empty(self):
        assert "https://www.example.com:80/" == self.obj.url_join("https://www.example.com:80", "")

    def test_url_join_basic(self):
        assert "https://www.example.com/nodes/node1" == self.obj.url_join(
            "https://www.example.com", "nodes", "node1"
        )

    def test_url_join_all_segments(self):
        assert "https://www.example.com/base/path#div1?search=query" == self.obj.url_join(
            "https://www.example.com/base#div1?search=query", "path"
        )

    def test_getattr_private(self):
        with pytest.raises(AttributeError) as exc_info:
            self.obj._thing

        print(exc_info)
        assert str(exc_info.value) == "_thing"

    def test_getattr_single(self):
        test_obj = core.ProxmoxResource(base_url=self.base_url)
        ret = test_obj.nodes

        assert isinstance(ret, core.ProxmoxResource)
        assert ret._store["base_url"] == self.base_url + "nodes"

    def test_call_basic(self):
        test_obj = core.ProxmoxResource(base_url=self.base_url)
        ret = test_obj("nodes")

        assert isinstance(ret, core.ProxmoxResource)
        assert ret._store["base_url"] == self.base_url + "nodes"

    def test_call_emptystr(self):
        test_obj = core.ProxmoxResource(base_url=self.base_url)
        ret = test_obj("")

        assert isinstance(ret, core.ProxmoxResource)
        assert ret._store["base_url"] == self.base_url

    def test_call_list(self):
        test_obj = core.ProxmoxResource(base_url=self.base_url)
        ret = test_obj(["nodes", "node1"])

        assert isinstance(ret, core.ProxmoxResource)
        assert ret._store["base_url"] == self.base_url + "nodes/node1"

    def test_call_stringable(self):
        test_obj = core.ProxmoxResource(base_url=self.base_url)

        class Thing(object):
            def __str__(self):
                return "string"

        ret = test_obj(Thing())

        assert isinstance(ret, core.ProxmoxResource)
        assert ret._store["base_url"] == self.base_url + "string"

    def test_request_basic_get(self, mock_resource, caplog):
        caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)

        ret = mock_resource._request("GET", params={"key": "value"})

        assert caplog.record_tuples == [
            (MODULE_LOGGER_NAME, logging.INFO, "GET " + self.base_url),
            (
                MODULE_LOGGER_NAME,
                logging.DEBUG,
                'Status code: 200, output: b\'{"data": {"key": "value"}}\'',
            ),
        ]

        assert ret == {"data": {"key": "value"}}

    def test_request_basic_post(self, mock_resource, caplog):
        caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)

        ret = mock_resource._request("POST", data={"key": "value"})

        assert caplog.record_tuples == [
            (
                MODULE_LOGGER_NAME,
                logging.INFO,
                "POST " + self.base_url + " " + str({"key": "value"}),
            ),
            (
                MODULE_LOGGER_NAME,
                logging.DEBUG,
                'Status code: 200, output: b\'{"data": {"key": "value"}}\'',
            ),
        ]
        assert ret == {"data": {"key": "value"}}

    def test_request_fail(self, mock_resource, caplog):
        caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)

        with pytest.raises(core.ResourceException) as exc_info:
            mock_resource("fail")._request("GET")

        assert caplog.record_tuples == [
            (
                MODULE_LOGGER_NAME,
                logging.INFO,
                "GET " + self.base_url + "fail",
            ),
            (
                MODULE_LOGGER_NAME,
                logging.DEBUG,
                "Status code: 500, output: b'this is the error'",
            ),
        ]
        assert exc_info.value.status_code == 500
        assert exc_info.value.status_message == "Internal Server Error"
        assert exc_info.value.content == str(b"this is the error")
        assert exc_info.value.errors is None

    def test_request_fail_with_reason(self, mock_resource, caplog):
        caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)

        with pytest.raises(core.ResourceException) as exc_info:
            mock_resource(["fail", "reason"])._request("GET")

        assert caplog.record_tuples == [
            (
                MODULE_LOGGER_NAME,
                logging.INFO,
                "GET " + self.base_url + "fail/reason",
            ),
            (
                MODULE_LOGGER_NAME,
                logging.DEBUG,
                "Status code: 500, output: b'this is the error'",
            ),
        ]
        assert exc_info.value.status_code == 500
        assert exc_info.value.status_message == "Internal Server Error"
        assert exc_info.value.content == "this is the reason"
        assert exc_info.value.errors == {"errors": b"this is the error"}

    def test_request_params_cleanup(self, mock_resource):
        mock_resource._request("GET", params={"key": "value", "remove_me": None})

        assert mock_resource._store["session"].params == {"key": "value"}

    def test_request_data_cleanup(self, mock_resource):
        mock_resource._request("POST", data={"key": "value", "remove_me": None})

        assert mock_resource._store["session"].data == {"key": "value"}


class TestProxmoxResourceMethods:
    _resource = core.ProxmoxResource(base_url="https://example.com")

    def test_get(self, mock_private_request):
        ret = self._resource.get("nodes", key="value")
        ret_self = ret["self"]

        assert ret["method"] == "GET"
        assert ret["params"] == {"key": "value"}
        assert ret_self._store["base_url"] == "https://example.com/nodes"

    def test_post(self, mock_private_request):
        ret = self._resource.post("nodes", key="value")
        ret_self = ret["self"]

        assert ret["method"] == "POST"
        assert ret["data"] == {"key": "value"}
        assert ret_self._store["base_url"] == "https://example.com/nodes"

    def test_put(self, mock_private_request):
        ret = self._resource.put("nodes", key="value")
        ret_self = ret["self"]

        assert ret["method"] == "PUT"
        assert ret["data"] == {"key": "value"}
        assert ret_self._store["base_url"] == "https://example.com/nodes"

    def test_delete(self, mock_private_request):
        ret = self._resource.delete("nodes", key="value")
        ret_self = ret["self"]

        assert ret["method"] == "DELETE"
        assert ret["params"] == {"key": "value"}
        assert ret_self._store["base_url"] == "https://example.com/nodes"

    def test_create(self, mock_private_request):
        ret = self._resource.create("nodes", key="value")
        ret_self = ret["self"]

        assert ret["method"] == "POST"
        assert ret["data"] == {"key": "value"}
        assert ret_self._store["base_url"] == "https://example.com/nodes"

    def test_set(self, mock_private_request):
        ret = self._resource.set("nodes", key="value")
        ret_self = ret["self"]

        assert ret["method"] == "PUT"
        assert ret["data"] == {"key": "value"}
        assert ret_self._store["base_url"] == "https://example.com/nodes"


class TestProxmoxAPI:
    def test_init_basic(self):
        prox = core.ProxmoxAPI(
            "host", token_name="name", token_value="value", service="pVe", backend="hTtPs"
        )

        assert isinstance(prox, core.ProxmoxAPI)
        assert isinstance(prox, core.ProxmoxResource)
        assert isinstance(prox._backend, https.Backend)
        assert prox._backend.auth.service == "PVE"

    def test_init_invalid_service(self):
        with pytest.raises(NotImplementedError) as exc_info:
            core.ProxmoxAPI("host", service="NA")

        assert str(exc_info.value) == "NA service is not supported"

    def test_init_invalid_backend(self):
        with pytest.raises(NotImplementedError) as exc_info:
            core.ProxmoxAPI("host", service="pbs", backend="LocaL")

        assert str(exc_info.value) == "PBS service does not support local backend"

    def test_init_local_with_host(self):
        with pytest.raises(NotImplementedError) as exc_info:
            core.ProxmoxAPI("host", service="pve", backend="LocaL")

        assert str(exc_info.value) == "local backend does not support host keyword"

    def test_get_tokens_https(self, mock_pve):
        prox = core.ProxmoxAPI("1.2.3.4:1234", user="user", password="password", backend="https")
        ticket, csrf = prox.get_tokens()

        assert ticket == "ticket"
        assert csrf == "CSRFPreventionToken"

    def test_get_tokens_local(self):
        prox = core.ProxmoxAPI(service="pve", backend="local")
        ticket, csrf = prox.get_tokens()

        assert ticket is None
        assert csrf is None


class MockSession:
    def request(self, method, url, data=None, params=None):
        # store the arguments in the session so they can be tested after the call
        self.data = data
        self.params = params
        self.method = method
        self.url = url

        if "fail" in url:
            r = Response(b"this is the error", 500)
            if "reason" in url:
                r.reason = "this is the reason"
            return r
        else:
            return Response(b'{"data": {"key": "value"}}', 200)


@pytest.fixture
def mock_private_request():
    def mock_request(self, method, data=None, params=None):
        return {"self": self, "method": method, "data": data, "params": params}

    with mock.patch("proxmoxer.core.ProxmoxResource._request", mock_request):
        yield


@pytest.fixture
def mock_resource():
    return core.ProxmoxResource(
        session=MockSession(), base_url="http://example.com/", serializer=JsonSimpleSerializer()
    )
