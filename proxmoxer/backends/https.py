__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"


import io
import json
import logging
import os
import platform
import sys
import time
from shlex import split as shell_split

from proxmoxer.core import SERVICES, AuthenticationError, config_failure

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)

STREAMING_SIZE_THRESHOLD = 10 * 1024 * 1024  # 10 MiB
SSL_OVERFLOW_THRESHOLD = 2147483135  # 2^31 - 1 - 512

try:
    import requests
    from requests.auth import AuthBase
    from requests.cookies import cookiejar_from_dict

    # Disable warnings about using untrusted TLS
    requests.packages.urllib3.disable_warnings()
except ImportError:
    logger.error("Chosen backend requires 'requests' module\n")
    sys.exit(1)


class ProxmoxHTTPAuthBase(AuthBase):
    def __call__(self, req):
        return req

    def get_cookies(self):
        return cookiejar_from_dict({})

    def get_tokens(self):
        return None, None

    def __init__(self, timeout=5, service="PVE", verify_ssl=False, cert=None):
        self.timeout = timeout
        self.service = service
        self.verify_ssl = verify_ssl
        self.cert = cert


class ProxmoxHTTPAuth(ProxmoxHTTPAuthBase):
    # number of seconds between renewing access tickets (must be less than 7200 to function correctly)
    # if calls are made less frequently than 2 hrs, using the API token auth is recommended
    renew_age = 3600

    def __init__(self, username, password, otp=None, base_url="", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.username = username
        self.pve_auth_ticket = ""

        self._get_new_tokens(password=password, otp=otp)

    def _get_new_tokens(self, password=None, otp=None):
        if password is None:
            # refresh from existing (unexpired) ticket
            password = self.pve_auth_ticket

        data = {"username": self.username, "password": password}
        if otp:
            data["otp"] = otp

        response_data = requests.post(
            self.base_url + "/access/ticket",
            verify=self.verify_ssl,
            timeout=self.timeout,
            data=data,
            cert=self.cert,
        ).json()["data"]
        if response_data is None:
            raise AuthenticationError(
                "Couldn't authenticate user: {0} to {1}".format(
                    self.username, self.base_url + "/access/ticket"
                )
            )
        if response_data.get("NeedTFA") is not None:
            raise AuthenticationError(
                "Couldn't authenticate user: missing Two Factor Authentication (TFA)"
            )

        self.birth_time = time.monotonic()
        self.pve_auth_ticket = response_data["ticket"]
        self.csrf_prevention_token = response_data["CSRFPreventionToken"]

    def get_cookies(self):
        return cookiejar_from_dict({self.service + "AuthCookie": self.pve_auth_ticket})

    def get_tokens(self):
        return self.pve_auth_ticket, self.csrf_prevention_token

    def __call__(self, req):
        # refresh ticket if older than `renew_age`
        time_diff = time.monotonic() - self.birth_time
        if time_diff >= self.renew_age:
            logger.debug(f"refreshing ticket (age {time_diff})")
            self._get_new_tokens()

        # only attach CSRF token if needed (reduce interception risk)
        if req.method != "GET":
            req.headers["CSRFPreventionToken"] = self.csrf_prevention_token
        return req


class ProxmoxHTTPApiTokenAuth(ProxmoxHTTPAuthBase):
    def __init__(self, username, token_name, token_value, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.token_name = token_name
        self.token_value = token_value

    def __call__(self, req):
        req.headers["Authorization"] = "{0}APIToken={1}!{2}{3}{4}".format(
            self.service,
            self.username,
            self.token_name,
            SERVICES[self.service]["token_separator"],
            self.token_value,
        )
        req.cert = self.cert
        return req


class JsonSerializer:
    content_types = [
        "application/json",
        "application/x-javascript",
        "text/javascript",
        "text/x-javascript",
        "text/x-json",
    ]

    def get_accept_types(self):
        return ", ".join(self.content_types)

    def loads(self, response):
        try:
            return json.loads(response.content.decode("utf-8"))["data"]
        except (UnicodeDecodeError, ValueError):
            return {"errors": response.content}

    def loads_errors(self, response):
        try:
            return json.loads(response.text).get("errors")
        except (UnicodeDecodeError, ValueError):
            return {"errors": response.content}


# pylint:disable=arguments-renamed
class ProxmoxHttpSession(requests.Session):
    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        stream=None,
        verify=None,
        cert=None,
        serializer=None,
    ):
        a = auth or self.auth
        c = cookies or self.cookies

        # set verify flag from auth if request does not have this parameter explicitly
        if verify is None:
            verify = a.verify_ssl

        if timeout is None:
            timeout = a.timeout

        # pull cookies from auth if not present
        if (not c) and a:
            cookies = a.get_cookies()

        # filter out streams
        files = files or {}
        data = data or {}
        total_file_size = 0
        for k, v in data.copy().items():
            # split qemu exec commands for proper parsing by PVE (issue#89)
            if k == "command" and url.endswith("agent/exec"):
                if isinstance(v, list):
                    data[k] = v
                elif "Windows" not in platform.platform():
                    data[k] = shell_split(v)
            if isinstance(v, io.IOBase):
                total_file_size += get_file_size(v)

                # add in filename from file pointer (patch for https://github.com/requests/toolbelt/pull/316)
                # add Content-Type since Proxmox requires it (https://bugzilla.proxmox.com/show_bug.cgi?id=4344)
                files[k] = (requests.utils.guess_filename(v), v, "application/octet-stream")
                del data[k]

        # if there are any large files, send all data and files using streaming multipart encoding
        if total_file_size > STREAMING_SIZE_THRESHOLD:
            try:
                # pylint:disable=import-outside-toplevel
                from requests_toolbelt import MultipartEncoder

                encoder = MultipartEncoder(fields={**data, **files})
                data = encoder
                files = None
                headers = {"Content-Type": encoder.content_type}
            except ImportError:
                # if the files will cause issues with the SSL 2GiB limit (https://bugs.python.org/issue42853#msg384566)
                if total_file_size > SSL_OVERFLOW_THRESHOLD:
                    logger.warning(
                        "Install 'requests_toolbelt' to add support for files larger than 2GiB"
                    )
                    raise OverflowError("Unable to upload a payload larger than 2 GiB")
                else:
                    logger.info(
                        "Installing 'requests_toolbelt' will decrease memory used during upload"
                    )

        return super().request(
            method,
            url,
            params,
            data,
            headers,
            cookies,
            files,
            auth,
            timeout,
            allow_redirects,
            proxies,
            hooks,
            stream,
            verify,
            cert,
        )


class Backend:
    def __init__(
        self,
        host,
        user=None,
        password=None,
        otp=None,
        port=None,
        verify_ssl=True,
        mode="json",
        timeout=5,
        token_name=None,
        token_value=None,
        path_prefix=None,
        service="PVE",
        cert=None,
    ):
        self.cert = cert
        host_port = ""
        if len(host.split(":")) > 2:  # IPv6
            if host.startswith("["):
                if "]:" in host:
                    host, host_port = host.rsplit(":", 1)
            else:
                host = f"[{host}]"
        elif ":" in host:
            host, host_port = host.split(":")
        port = host_port if host_port.isdigit() else port

        # if a port is not specified, use the default port for this service
        if not port:
            port = SERVICES[service]["default_port"]

        self.mode = mode
        if path_prefix is not None:
            self.base_url = f"https://{host}:{port}/{path_prefix}/api2/{mode}"
        else:
            self.base_url = f"https://{host}:{port}/api2/{mode}"

        if token_name is not None:
            if "token" not in SERVICES[service]["supported_https_auths"]:
                config_failure("{} does not support API Token authentication", service)

            self.auth = ProxmoxHTTPApiTokenAuth(
                user,
                token_name,
                token_value,
                verify_ssl=verify_ssl,
                timeout=timeout,
                service=service,
                cert=self.cert,
            )
        elif password is not None:
            if "password" not in SERVICES[service]["supported_https_auths"]:
                config_failure("{} does not support password authentication", service)

            self.auth = ProxmoxHTTPAuth(
                user,
                password,
                otp,
                base_url=self.base_url,
                verify_ssl=verify_ssl,
                timeout=timeout,
                service=service,
                cert=self.cert,
            )
        else:
            config_failure("No valid authentication credentials were supplied")

    def get_session(self):
        session = ProxmoxHttpSession()
        session.cert = self.cert
        session.auth = self.auth
        # cookies are taken from the auth
        session.headers["Connection"] = "keep-alive"
        session.headers["accept"] = self.get_serializer().get_accept_types()
        return session

    def get_base_url(self):
        return self.base_url

    def get_serializer(self):
        assert self.mode == "json"
        return JsonSerializer()

    def get_tokens(self):
        """Return the in-use auth and csrf tokens if using user/password auth."""
        return self.auth.get_tokens()


def get_file_size(file_obj):
    """Returns the number of bytes in the given file object in total
    file cursor remains at the same location as when passed in

    :param fileObj: file object of which the get size
    :type fileObj: file object
    :return: total bytes in file object
    :rtype: int
    """
    # store existing file cursor location
    starting_cursor = file_obj.tell()

    # seek to end of file
    file_obj.seek(0, os.SEEK_END)

    size = file_obj.tell()

    # reset cursor
    file_obj.seek(starting_cursor)

    return size


def get_file_size_partial(file_obj):
    """Returns the number of bytes in the given file object from the current cursor to the end

    :param fileObj: file object of which the get size
    :type fileObj: file object
    :return: remaining bytes in file object
    :rtype: int
    """
    # store existing file cursor location
    starting_cursor = file_obj.tell()

    file_obj.seek(0, os.SEEK_END)

    # get number of byte between where the cursor was set and the end
    size = file_obj.tell() - starting_cursor

    # reset cursor
    file_obj.seek(starting_cursor)

    return size
