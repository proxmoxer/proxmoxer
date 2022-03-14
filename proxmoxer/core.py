__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"

# spell-checker:ignore urlunsplit

import importlib
import logging
import posixpath

# Python 3 compatibility:
try:
    import httplib
except ImportError:  # py3
    from http import client as httplib
try:
    import urlparse
except ImportError:  # py3
    from urllib import parse as urlparse
try:
    basestring
except NameError:  # py3
    basestring = (bytes, str)

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)


# https://metacpan.org/pod/AnyEvent::HTTP
ANYEVENT_HTTP_STATUS_CODES = {
    595: "Errors during connection establishment, proxy handshake",
    596: "Errors during TLS negotiation, request sending and header processing",
    597: "Errors during body receiving or processing",
    598: "User aborted request via on_header or on_body",
    599: "Other, usually nonretryable, errors (garbled URL etc.)",
}

SERVICES = {
    "PVE": {
        "supported_backends": ["local", "https", "openssh", "ssh_paramiko"],
        "supported_https_auths": ["password", "token"],
        "default_port": 8006,
        "token_separator": "=",
        "ssh_additional_options": ["--output-format", "json"],
    },
    "PMG": {
        "supported_backends": ["local", "https", "openssh", "ssh_paramiko"],
        "supported_https_auths": ["password"],
        "default_port": 8006,
    },
    "PBS": {
        "supported_backends": ["https"],
        "supported_https_auths": ["password", "token"],
        "default_port": 8007,
        "token_separator": ":",
    },
}


def config_failure(message, *args):
    raise NotImplementedError(message.format(*args))


class ProxmoxResourceBase(object):
    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError(item)

        kwargs = self._store.copy()
        kwargs["base_url"] = self.url_join(self._store["base_url"], item)

        return ProxmoxResource(**kwargs)

    def url_join(self, base, *args):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(base)
        path = path if len(path) else "/"
        path = posixpath.join(path, *[("%s" % x) for x in args])
        return urlparse.urlunsplit([scheme, netloc, path, query, fragment])


class ResourceException(Exception):
    def __init__(self, status_code, status_message, content, errors=None):
        self.status_code = status_code
        self.status_message = status_message
        self.content = content
        self.errors = errors
        if errors is not None:
            content += " - {0}".format(errors)
        message = "{0} {1}: {2}".format(status_code, status_message, content).strip()
        super(ResourceException, self).__init__(message)


class ProxmoxResource(ProxmoxResourceBase):
    def __init__(self, **kwargs):
        self._store = kwargs

    def __call__(self, resource_id=None):
        if not resource_id:
            return self

        if isinstance(resource_id, basestring):
            resource_id = resource_id.split("/")
        elif not isinstance(resource_id, (tuple, list)):
            resource_id = [str(resource_id)]

        kwargs = self._store.copy()
        if resource_id is not None:
            kwargs["base_url"] = self.url_join(self._store["base_url"], *resource_id)

        return ProxmoxResource(**kwargs)

    def _request(self, method, data=None, params=None):
        url = self._store["base_url"]
        if data:
            logger.info("%s %s %r", method, url, data)
        else:
            logger.info("%s %s", method, url)
        resp = self._store["session"].request(method, url, data=data or None, params=params)
        logger.debug("Status code: %s, output: %s", resp.status_code, resp.content)

        if resp.status_code >= 400:
            if hasattr(resp, "reason"):
                raise ResourceException(
                    resp.status_code,
                    httplib.responses.get(
                        resp.status_code, ANYEVENT_HTTP_STATUS_CODES.get(resp.status_code)
                    ),
                    resp.reason,
                    errors=(self._store["serializer"].loads_errors(resp) or {}),
                )
            else:
                raise ResourceException(
                    resp.status_code,
                    httplib.responses.get(
                        resp.status_code, ANYEVENT_HTTP_STATUS_CODES.get(resp.status_code)
                    ),
                    resp.text,
                )
        elif 200 <= resp.status_code <= 299:
            return self._store["serializer"].loads(resp)

    def get(self, *args, **params):
        return self(args)._request("GET", params=params)

    def post(self, *args, **data):
        return self(args)._request("POST", data=data)

    def put(self, *args, **data):
        return self(args)._request("PUT", data=data)

    def delete(self, *args, **params):
        return self(args)._request("DELETE", params=params)

    def create(self, *args, **data):
        return self.post(*args, **data)

    def set(self, *args, **data):
        return self.put(*args, **data)


class ProxmoxAPI(ProxmoxResource):
    def __init__(self, host=None, backend="https", service="PVE", **kwargs):
        super(ProxmoxAPI, self).__init__(**kwargs)
        service = service.upper()
        backend = backend.lower()

        # throw error for unsupported services
        if service not in SERVICES.keys():
            config_failure("{} service is not supported", service)

        # throw error for unsupported backend for service
        if backend not in SERVICES[service]["supported_backends"]:
            config_failure("{} backend does not support {} backend", service, backend)

        if host is not None:
            if backend == "local":
                config_failure("{} backend does not support host keyword", backend)
            else:
                kwargs["host"] = host

        kwargs["service"] = service

        # load backend module
        self._backend = importlib.import_module(".backends.%s" % backend, "proxmoxer").Backend(
            **kwargs
        )
        self._backend_name = backend

        self._store = {
            "base_url": self._backend.get_base_url(),
            "session": self._backend.get_session(),
            "serializer": self._backend.get_serializer(),
        }

    def get_tokens(self):
        """Return the auth and csrf tokens.

        Returns (None, None) if the backend is not https using password authentication.
        """
        if self._backend_name != "https":
            return None, None

        return self._backend.get_tokens()
