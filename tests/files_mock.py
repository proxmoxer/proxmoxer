__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2022"
__license__ = "MIT"

import re

import pytest
import responses
from requests import exceptions

from .api_mock import PVERegistry


@pytest.fixture()
def mock_files():
    with responses.RequestsMock(
        registry=FilesRegistry, assert_all_requests_are_fired=False
    ) as rsps:
        yield rsps


class FilesRegistry(responses.registries.FirstMatchRegistry):
    base_url = "https://sub.domain.tld"

    common_headers = {
        "Cache-Control": "max-age=0",
        "Connection": "close, Keep-Alive",
        "Pragma": "no-cache",
        "Server": "pve-api-daemon/3.0",
        "Content-Type": "application/json;charset=UTF-8",
    }

    def __init__(self):
        super().__init__()
        for resp in self._generate_static_responses():
            self.add(resp)

        for resp in self._generate_dynamic_responses():
            self.add(resp)

    def _generate_static_responses(self):
        resps = []

        # Basic GET requests
        resps.append(responses.Response(method="GET", url=self.base_url, body="hello world"))
        resps.append(
            responses.Response(method="GET", url=self.base_url + "/file.iso", body="CONTENTS")
        )

        # sibling
        resps.append(
            responses.Response(
                method="GET", url=self.base_url + "/sibling/file.iso", body="CONTENTS\n"
            )
        )
        resps.append(
            responses.Response(
                method="GET",
                url=self.base_url + "/sibling/TESTINGSUMS",
                body="this_is_the_hash  file.iso",
            )
        )

        # extension
        resps.append(
            responses.Response(
                method="GET", url=self.base_url + "/extension/file.iso", body="CONTENTS\n"
            )
        )
        resps.append(
            responses.Response(
                method="GET",
                url=self.base_url + "/extension/file.iso.testing",
                body="this_is_the_hash  file.iso",
            )
        )
        resps.append(
            responses.Response(
                method="GET",
                url=self.base_url + "/extension/connectionerror.iso.testing",
                body=exceptions.ConnectionError(),
            )
        )
        resps.append(
            responses.Response(
                method="GET",
                url=self.base_url + "/extension/readtimeout.iso.testing",
                body=exceptions.ReadTimeout(),
            )
        )

        # extension upper
        resps.append(
            responses.Response(
                method="GET", url=self.base_url + "/upper/file.iso", body="CONTENTS\n"
            )
        )
        resps.append(
            responses.Response(
                method="GET",
                url=self.base_url + "/upper/file.iso.TESTING",
                body="this_is_the_hash  file.iso",
            )
        )

        resps.append(
            responses.Response(
                method="GET",
                url=re.compile(self.base_url + r"/checksums/file.iso.\w+"),
                body="1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890 file.iso",
            )
        )

        return resps

    def _generate_dynamic_responses(self):
        resps = []

        resps.append(
            responses.CallbackResponse(
                method="POST",
                url=re.compile(self.base_url + r"/checksums/\w+/file.iso.\w+"),
                callback=self._cb_multi_checksum,
            )
        )

        return resps

    ###################################
    # Callbacks for Dynamic Responses #
    ###################################

    def _cb_multi_checksum(self, request):
        m = re.match(self.base_url + r"/checksums/(\w+)/file.iso.(\w+)", request.url)
        checksum_name = m.group(1)
        checksum_ext = m.group(2)

        if checksum_ext == checksum_name:
            return (
                200,
                self.common_headers,
                "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890 file.iso",
            )

        return (404, self.common_headers, "")


@pytest.fixture()
def mock_files_and_pve():
    with responses.RequestsMock(registry=BothRegistry, assert_all_requests_are_fired=False) as rsps:
        yield rsps


class BothRegistry(responses.registries.FirstMatchRegistry):
    def __init__(self):
        super().__init__()
        registries = [FilesRegistry(), PVERegistry()]

        for reg in registries:
            for resp in reg.registered:
                self.add(resp)
