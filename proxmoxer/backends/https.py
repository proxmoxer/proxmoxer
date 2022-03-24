__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"


import io
import json
import logging
import os
import sys
import time
from shlex import split as shell_split

from proxmoxer.core import SERVICES, config_failure

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)

STREAMING_SIZE_THRESHOLD = 100 * 1024 * 1024  # 10 MiB

# fmt: off
try:
    import requests
    from requests.auth import AuthBase
    from requests.cookies import cookiejar_from_dict
except ImportError:
    logger.error("Chosen backend requires 'requests' module\n")
    sys.exit(1)


def is_file(obj): return isinstance(obj, io.IOBase)
def get_time(): return time.monotonic()
# fmt: on


class AuthenticationError(Exception):
    def __init__(self, msg):
        super(AuthenticationError, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.__str__()


class ProxmoxHTTPAuthBase(AuthBase):
    def __call__(self, req):
        return req

    def get_cookies(self):
        return cookiejar_from_dict({})

    def get_tokens(self):
        return None, None

    def __init__(self, timeout=5, service="PVE", verify_ssl=False):
        self.timeout = timeout
        self.service = service
        self.verify_ssl = verify_ssl


class ProxmoxHTTPAuth(ProxmoxHTTPAuthBase):
    # number of seconds between renewing access tickets (must be less than 7200 to function correctly)
    # if calls are made less frequently than 2 hrs, using the API token auth is reccomended
    renew_age = 3600

    def __init__(self, username, password, otp=None, base_url="", **kwargs):
        super(ProxmoxHTTPAuth, self).__init__(**kwargs)
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
        ).json()["data"]
        if response_data is None:
            raise AuthenticationError(
                "Couldn't authenticate user: {0} to {1}".format(
                    self.username, self.base_url + "/access/ticket"
                )
            )

        self.birth_time = get_time()
        self.pve_auth_ticket = response_data["ticket"]
        self.csrf_prevention_token = response_data["CSRFPreventionToken"]

    def get_cookies(self):
        return cookiejar_from_dict({self.service + "AuthCookie": self.pve_auth_ticket})

    def get_tokens(self):
        return self.pve_auth_ticket, self.csrf_prevention_token

    def __call__(self, req):
        # refresh ticket if older than `renew_age`
        if (get_time() - self.birth_time) >= self.renew_age:
            logger.debug("refreshing ticket (age {0})".format(get_time() - self.birth_time))
            self._get_new_tokens()

        # only attach CSRF token if needed (reduce interception risk)
        if req.method != "GET":
            req.headers["CSRFPreventionToken"] = self.csrf_prevention_token
        return req


# DEPRECATED(1.1.0) - either use a password or the API Tokens
class ProxmoxHTTPTicketAuth(ProxmoxHTTPAuth):
    """Use existing ticket/token to create a session.

    Overrides ProxmoxHTTPAuth so that an existing auth ticket and csrf token
    may be used instead of passing username/password.
    """

    def __init__(self, auth_ticket, csrf_token):
        self.pve_auth_ticket = auth_ticket
        self.csrf_prevention_token = csrf_token
        self.birth_time = get_time()

        # deprecation notice
        logger.warning(
            "** Existing token auth is Deprecated as of 1.1.0\n** Please use the API Token Auth for long-running programs or pass existing ticket as password to the user/password auth"
        )


class ProxmoxHTTPApiTokenAuth(ProxmoxHTTPAuthBase):
    def __init__(self, username, token_name, token_value, service, **kwargs):
        super(ProxmoxHTTPApiTokenAuth, self).__init__(**kwargs)
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
        return req


class JsonSerializer(object):
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
            return json.loads(response.text)["errors"]
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

        # take set verify flag from auth if request does not have this parameter explicitly
        if verify is None:
            verify = a.verify

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
            if k == "command":
                data[k] = v if isinstance(v, list) else shell_split(v)
            if is_file(v):
                total_file_size += get_file_size(v)

                # add in filename from file pointer (patch for https://github.com/requests/toolbelt/pull/316)
                files[k] = (requests.utils.guess_filename(v), v)
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
                if total_file_size > 2147483135:  # 2^31 - 1 - 512
                    logger.warning(
                        "Install 'requests_toolbelt' to add support for files larger than 2GiB"
                    )
                    raise OverflowError("Unable to upload a payload larger than 2 GiB")
                else:
                    logger.info(
                        "Installing 'requests_toolbelt' will deacrease memory used during upload"
                    )

        if not files and serializer:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

        return super(ProxmoxHttpSession, self).request(
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


class Backend(object):
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
        auth_token=None,
        csrf_token=None,
        token_name=None,
        token_value=None,
        service="PVE",
        # TODO jhollowe allow adding a path prefix
    ):

        host_port = ""
        if len(host.split(":")) > 2:  # IPv6
            if host.startswith("["):
                if "]:" in host:
                    host, host_port = host.rsplit(":", 1)
            else:
                host = "[{0}]".format(host)
        elif ":" in host:
            host, host_port = host.split(":")
        port = host_port if host_port.isdigit() else port

        # if a port is not specified, use the default port for this service
        if not port:
            port = SERVICES[service]["default_port"]

        self.mode = mode
        self.base_url = "https://{0}:{1}/api2/{2}".format(host, port, mode)

        if auth_token is not None:
            # DEPRECATED(1.1.0) - either use a password or the API Tokens
            self.auth = ProxmoxHTTPTicketAuth(auth_token, csrf_token)
        elif token_name is not None:
            if "token" not in SERVICES[service]["supported_https_auths"]:
                config_failure("{} does not support API Token authentication", service)

            self.auth = ProxmoxHTTPApiTokenAuth(user, token_name, token_value, service=service)
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
            )

    def get_session(self):
        session = ProxmoxHttpSession()
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
