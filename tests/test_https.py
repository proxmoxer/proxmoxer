# import pytest
import proxmoxer.backends.https as https


class TestHttpsBackend:
    """
    Tests for the proxmox.backends.https file.
    Includes test of Backend, Session, and Auths
    """

    # def test_init(self):
    #     pass


class TestJsonSerializer:
    _serializer = https.JsonSerializer()

    def test_get_accept_types(self):
        ctypes = "application/json, application/x-javascript, text/javascript, text/x-javascript, text/x-json"
        assert self._serializer.get_accept_types() == ctypes
