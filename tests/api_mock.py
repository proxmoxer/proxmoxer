__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2022"
__license__ = "MIT"

import json
import re
from urllib.parse import parse_qsl, urlparse

import pytest
import responses
from requests_toolbelt import MultipartEncoder


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
        resps.append(
            responses.Response(
                method="GET",
                url=self.base_url + "/version",
                json={"data": {"version": "7.2-3", "release": "7.2", "repoid": "c743d6c1"}},
            )
        )

        resps.append(
            responses.Response(
                method="POST",
                url=re.compile(self.base_url + r"/nodes/[^/]+/storage/[^/]+/download-url"),
                # "done" added to UPID so polling will terminate (status checking is tested elsewhere)
                json={
                    "data": "UPID:node:003094EA:095F1EFE:63E88772:download:file.iso:root@pam:done",
                    "success": 1,
                },
            )
        )

        resps.append(
            responses.Response(
                method="POST",
                url=re.compile(self.base_url + r"/nodes/[^/]+/storage/storage1/upload"),
                # "done" added to UPID so polling will terminate (status checking is tested elsewhere)
                json={"data": "UPID:node:0017C594:0ADB2769:63EC5455:imgcopy::root@pam:done"},
            )
        )
        resps.append(
            responses.Response(
                method="POST",
                url=re.compile(self.base_url + r"/nodes/[^/]+/storage/missing/upload"),
                status=500,
                body="storage 'missing' does not exist",
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

        # Session testing
        resps.append(
            responses.CallbackResponse(
                method="GET",
                url=self.base_url + "/fake/echo",
                callback=self._cb_echo,
            )
        )

        resps.append(
            responses.CallbackResponse(
                method="GET",
                url=re.compile(self.base_url + r"/nodes/[^/]+/qemu/[^/]+/agent/exec"),
                callback=self._cb_echo,
            )
        )

        resps.append(
            responses.CallbackResponse(
                method="GET",
                url=re.compile(self.base_url + r"/nodes/[^/]+/qemu/[^/]+/monitor"),
                callback=self._cb_qemu_monitor,
            )
        )

        resps.append(
            responses.CallbackResponse(
                method="GET",
                url=re.compile(self.base_url + r"/nodes/[^/]+/tasks/[^/]+/status"),
                callback=self._cb_task_status,
            )
        )

        resps.append(
            responses.CallbackResponse(
                method="GET",
                url=re.compile(self.base_url + r"/nodes/[^/]+/query-url-metadata.*"),
                callback=self._cb_url_metadata,
            )
        )

        return resps

    ###################################
    # Callbacks for Dynamic Responses #
    ###################################

    def _cb_echo(self, request):
        body = request.body
        if body is not None:
            if isinstance(body, MultipartEncoder):
                body = body.to_string()  # really, to byte string
            body = body if isinstance(body, str) else str(body, "utf-8")

        resp = {
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "cookies": request._cookies.get_dict(),
            "body": body,
            # "body_json": dict(parse_qsl(request.body)),
        }
        return (200, self.common_headers, json.dumps(resp))

    def _cb_password_auth(self, request):
        form_data_dict = dict(parse_qsl(request.body))

        # if this user should not be authenticated
        if form_data_dict.get("username") == "bad_auth":
            return (
                401,
                self.common_headers,
                json.dumps({"data": None}),
            )
        # if this user requires OTP and it is not included
        if form_data_dict.get("username") == "otp" and not "tfa-challenge" in form_data_dict:
            return (
                200,
                self.common_headers,
                json.dumps(
                    {
                        "data": {
                            "ticket": "otp_ticket",
                            "CSRFPreventionToken": "CSRFPreventionToken",
                            "NeedTFA": 1,
                        }
                    }
                ),
            )
        # if OTP key is not valid
        elif form_data_dict.get("username") == "otp" and form_data_dict.get("tfa-challenge") == "otp_ticket":
            if form_data_dict.get('password') == "totp:123456":
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
            else:
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

    def _cb_task_status(self, request):
        resp = {}
        if "keep-running" in request.url:
            resp = {
                "data": {
                    "id": "110",
                    "pid": 1044989,
                    "node": "node1",
                    "pstart": 284768076,
                    "status": "running",
                    "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running",
                    "starttime": 1661825068,
                    "user": "root@pam",
                    "type": "vzdump",
                }
            }

        elif "stopped" in request.url:
            resp = {
                "data": {
                    "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:stopped",
                    "starttime": 1661825068,
                    "user": "root@pam",
                    "type": "vzdump",
                    "pstart": 284768076,
                    "status": "stopped",
                    "exitstatus": "interrupted by signal",
                    "pid": 1044989,
                    "id": "110",
                    "node": "node1",
                }
            }

        elif "done" in request.url:
            resp = {
                "data": {
                    "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:done",
                    "starttime": 1661825068,
                    "user": "root@pam",
                    "type": "vzdump",
                    "pstart": 284768076,
                    "status": "stopped",
                    "exitstatus": "OK",
                    "pid": 1044989,
                    "id": "110",
                    "node": "node1",
                }
            }

        elif "comment" in request.url:
            resp = {
                "data": {
                    "upid": "UPID:node:00000000:00000000:00000000:task:id:root@pam:comment",
                    "node": "node",
                    "pid": 0,
                    "pstart": 0,
                    "starttime": 0,
                    "type": "task",
                    "id": "id",
                    "user": "root@pam",
                    "status": "stopped",
                    "exitstatus": "OK",
                }
            }

        return (200, self.common_headers, json.dumps(resp))

    def _cb_url_metadata(self, request):
        form_data_dict = dict(parse_qsl((urlparse(request.url)).query))

        if "file.iso" in form_data_dict.get("url", ""):
            return (
                200,
                self.common_headers,
                json.dumps(
                    {
                        "data": {
                            "size": 123456,
                            "filename": "file.iso",
                            "mimetype": "application/x-iso9660-image",
                            # "mimetype": "application/octet-stream",
                        },
                        "success": 1,
                    }
                ),
            )
        elif "invalid.iso" in form_data_dict.get("url", ""):
            return (
                500,
                self.common_headers,
                json.dumps(
                    {
                        "status": 500,
                        "message": "invalid server response: '500 Can't connect to sub.domain.tld:443 (certificate verify failed)'\n",
                        "success": 0,
                        "data": None,
                    }
                ),
            )
        elif "missing.iso" in form_data_dict.get("url", ""):
            return (
                500,
                self.common_headers,
                json.dumps(
                    {
                        "status": 500,
                        "success": 0,
                        "message": "invalid server response: '404 Not Found'\n",
                        "data": None,
                    }
                ),
            )

        elif "index.html" in form_data_dict.get("url", ""):
            return (
                200,
                self.common_headers,
                json.dumps(
                    {
                        "success": 1,
                        "data": {"filename": "index.html", "mimetype": "text/html", "size": 17664},
                    }
                ),
            )

    def _cb_qemu_monitor(self, request):
        body = request.body
        if body is not None:
            body = body if isinstance(body, str) else str(body, "utf-8")

        # if the command is an array, throw the type error PVE would throw
        if "&" in body:
            return (
                400,
                self.common_headers,
                json.dumps(
                    {
                        "data": None,
                        "errors": {"command": "type check ('string') failed - got ARRAY"},
                    }
                ),
            )
        else:
            resp = {
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers),
                "cookies": request._cookies.get_dict(),
                "body": body,
                # "body_json": dict(parse_qsl(request.body)),
            }
            print(resp)
            return (200, self.common_headers, json.dumps(resp))
