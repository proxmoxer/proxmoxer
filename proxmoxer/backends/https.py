__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2017'
__licence__ = 'MIT'


import json
import sys
import time

try:
    import requests
    urllib3 = requests.packages.urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from requests.auth import AuthBase
    from requests.cookies import cookiejar_from_dict
except ImportError:
    import sys
    sys.stderr.write("Chosen backend requires 'requests' module\n")
    sys.exit(1)


if sys.version_info[0] >= 3:
    import io
    def is_file(obj): return isinstance(obj, io.IOBase)
else:
    def is_file(obj): return isinstance(obj, file)


class AuthenticationError(Exception):
    def __init__(self, msg):
        super(AuthenticationError, self).__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.__str__()


class ProxmoxHTTPAuth(AuthBase):
    # number of seconds between renewing access tokens (must be less than 7200 to function correctly)
    renew_age = 3600

    def __init__(self, base_url, username, password, verify_ssl=False, timeout=5, long_running=False):
        self.base_url = base_url
        self.username = username
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.pve_auth_cookie = ""
        self.password = ""

        # if there will be periods greater than 2hrs between calls, store the password as we cannot renew the token
        if long_running:
            self.password = password

        self._getNewTokens(password=password)


    def _getNewTokens(self, password=None):
        if password == None:
            password = self.pve_auth_cookie
        if self.password:
            password = self.password

        response_data = requests.post(self.base_url + "/access/ticket",
                                      verify=self.verify_ssl,
                                      timeout=self.timeout,
                                      data={"username": self.username, "password": password}).json()["data"]
        if response_data is None:
            raise AuthenticationError("Couldn't authenticate user: {0} to {1}".format(self.username, self.base_url + "/access/ticket"))

        self.birth_time = time.time()
        self.pve_auth_cookie = response_data["ticket"]
        self.csrf_prevention_token = response_data["CSRFPreventionToken"]


    def __call__(self, r):
        #refresh token if older than `renew_age`
        if (time.time() - self.birth_time) >= self.renew_age:
            self._getNewTokens()

        r.headers["CSRFPreventionToken"] = self.csrf_prevention_token
        return r


class ProxmoxHTTPTokenAuth(ProxmoxHTTPAuth):
    """Use existing ticket/token to create a session.

    Overrides ProxmoxHTTPAuth so that an existing auth cookie and csrf token
    may be used instead of passing username/password.
    """
    def __init__(self, auth_token, csrf_token):
        self.pve_auth_cookie = auth_token
        self.csrf_prevention_token = csrf_token


class JsonSerializer(object):

    content_types = [
        "application/json",
        "application/x-javascript",
        "text/javascript",
        "text/x-javascript",
        "text/x-json"
        ]

    def get_accept_types(self):
        return ", ".join(self.content_types)

    def loads(self, response):
        try:
            return json.loads(response.content.decode('utf-8'))['data']
        except (UnicodeDecodeError, ValueError):
            return response.content


class ProxmoxHttpSession(requests.Session):

    def request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None,
                serializer=None):

        # take set verify flag from session if request does not have this parameter explicitly
        if verify is None:
            verify = self.verify

        #filter out streams
        files = files or {}
        data = data or {}
        for k, v in data.copy().items():
            if is_file(v):
                files[k] = v
                del data[k]

        headers = None
        if not files and serializer:
            headers = {"content-type": 'application/x-www-form-urlencoded'}

        return super(ProxmoxHttpSession, self).request(method, url, params, data, headers, cookies, files, auth,
                                                       timeout, allow_redirects, proxies, hooks, stream, verify, cert)


class Backend(object):
    def __init__(self, host, user, password, port=8006, verify_ssl=True,
                 mode='json', timeout=5, long_running=False, auth_token=None, csrf_token=None):
        if ':' in host:
            host, host_port = host.split(':')
            port = host_port if host_port.isdigit() else port

        self.base_url = "https://{0}:{1}/api2/{2}".format(host, port, mode)

        if auth_token is not None:
            self.auth = ProxmoxHTTPTokenAuth(auth_token, csrf_token)
        else:
            self.auth = ProxmoxHTTPAuth(self.base_url, user, password, verify_ssl, timeout, long_running)
        self.verify_ssl = verify_ssl
        self.mode = mode
        self.timeout = timeout

    def get_session(self):
        session = ProxmoxHttpSession()
        session.verify = self.verify_ssl
        session.auth = self.auth
        session.cookies = cookiejar_from_dict({"PVEAuthCookie": self.auth.pve_auth_cookie})
        session.headers['Connection'] = 'keep-alive'
        session.headers["accept"] = self.get_serializer().get_accept_types()
        return session

    def get_base_url(self):
        return self.base_url

    def get_serializer(self):
        assert self.mode == 'json'
        return JsonSerializer()

    def get_tokens(self):
        """Return the in-use auth and csrf tokens."""
        return self.auth.pve_auth_cookie, self.auth.csrf_prevention_token
