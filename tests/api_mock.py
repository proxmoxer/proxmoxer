import json
from urllib.parse import parse_qsl

import pytest
import responses


@pytest.fixture()
def mock_pve():
    with responses.RequestsMock(registry=PVERegistry, assert_all_requests_are_fired=False) as rsps:
        yield rsps


class PVERegistry(responses.registries.FirstMatchRegistry):
    base_url = "https://1.2.3.4:1234/api2/json"

    common_headers = {
        "Cache-Control": "max-age=0",
        "Connection": "close, Keep-Alive",
        "Pragma": "no-cache",
        "Server": "pve-api-daemon/3.0",
        "Content-Type": "application/json;charset=UTF-8",
        # "Content-Encoding": "gzip",
    }

    def __init__(self):
        super().__init__()
        for resp in self._generate_static_responses():
            self.add(resp)

        for resp in self._generate_dynamic_responses():
            self.add(resp)

    def set_base_url(self, base_url):
        self.base_url = base_url

    def _generate_static_responses(self):
        resps = []

        # Basic GET requests
        resps.append(
            responses.Response(
                method="GET",
                url=self.base_url + "/version",
                json={"data": {"version": "7.2-3", "release": "7.2", "repoid": "c743d6c1"}},
            )
        )

        return resps

    def _generate_dynamic_responses(self):
        resps = []

        # Authentication
        resps.append(
            responses.CallbackResponse(
                method="POST",
                url=self.base_url + "/access/ticket",
                callback=self._cb_password_auth,
            )
        )

        return resps

    ###################################
    # Callbacks for Dynamic Responses #
    ###################################

    def _cb_password_auth(self, request):
        form_data_dict = dict(parse_qsl(request.body))

        # if this user should not be authenticated
        if form_data_dict.get("username") == "bad_auth":
            return (
                401,
                self.common_headers,
                json.dumps({"data": None}),
            )

        # if this is the first ticket
        if form_data_dict.get("password") != "ticket":
            return (
                200,
                self.common_headers,
                json.dumps(
                    {"data": {"ticket": "ticket", "CSRFPreventionToken": "CSRFPreventionToken"}}
                ),
            )
        # if this is refreshing the ticket, return new ticket
        else:
            return (
                200,
                self.common_headers,
                json.dumps(
                    {
                        "data": {
                            "ticket": "new_ticket",
                            "CSRFPreventionToken": "CSRFPreventionToken_2",
                        }
                    }
                ),
            )
