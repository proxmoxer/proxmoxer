__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"


import json
import logging
import platform
import re
from itertools import chain
from shlex import split as shell_split

from proxmoxer.core import SERVICES

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)


try:
    from shlex import join

    def shell_join(args):
        return join(args)

except ImportError:
    from shlex import quote

    def shell_join(args):
        return " ".join([quote(arg) for arg in args])


class Response(object):
    def __init__(self, content, status_code):
        self.status_code = status_code
        self.content = content
        self.text = str(content)
        self.headers = {"content-type": "application/json"}

    def __str__(self):
        return f"Response ({self.status_code}) {self.content}"


class CommandBaseSession(object):
    def __init__(
        self,
        service="PVE",
        timeout=5,
        sudo=False,
    ):
        self.service = service.lower()
        self.timeout = timeout
        self.sudo = sudo

    def _exec(self, cmd):
        raise NotImplementedError()

    # noinspection PyUnusedLocal
    def request(self, method, url, data=None, params=None, headers=None):
        method = method.lower()
        data = data or {}
        params = params or {}
        url = url.strip()

        cmd = {"post": "create", "put": "set"}.get(method, method)

        # separate out qemu exec commands to split into multiple argument pairs (issue#89)
        data_command = None
        if "/agent/exec" in url:
            data_command = data.get("command")
            if data_command is not None:
                del data["command"]

        # for 'upload' call some workaround
        tmp_filename = ""
        if url.endswith("upload"):
            # copy file to temporary location on proxmox host
            tmp_filename, _ = self._exec(
                [
                    "python3",
                    "-c",
                    "import tempfile; import sys; tf = tempfile.NamedTemporaryFile(); sys.stdout.write(tf.name)",
                ]
            )
            tmp_filename = str(tmp_filename, "utf-8")
            self.upload_file_obj(data["filename"], tmp_filename)
            data["filename"] = data["filename"].name
            data["tmpfilename"] = tmp_filename

        command = [f"{self.service}sh", cmd, url]
        # convert the options dict into a 2-tuple with the key formatted as a flag
        option_pairs = [(f"-{k}", str(v)) for k, v in chain(data.items(), params.items())]
        # add back in all the command arguments as their own pairs
        if data_command is not None:
            if isinstance(data_command, list):
                command_arr = data_command
            elif "Windows" not in platform.platform():
                command_arr = shell_split(data_command)
            for arg in command_arr:
                option_pairs.append(("-command", arg))
        # expand the list of 2-tuples into a flat list
        options = [val for pair in option_pairs for val in pair]
        additional_options = SERVICES[self.service.upper()].get("cli_additional_options", [])
        full_cmd = command + options + additional_options

        if self.sudo:
            full_cmd = ["sudo"] + full_cmd

        stdout, stderr = self._exec(full_cmd)

        def is_http_status_string(s):
            return re.match(r"\d\d\d [a-zA-Z]", str(s))

        if stderr:
            # sometimes contains extra text like 'trying to acquire lock...OK'
            status_code = next(
                (
                    int(line.split()[0])
                    for line in stderr.splitlines()
                    if is_http_status_string(line)
                ),
                500,
            )
        else:
            status_code = 200
        if stdout:
            return Response(stdout, status_code)
        return Response(stderr, status_code)

    def upload_file_obj(self, file_obj, remote_path):
        raise NotImplementedError()


class JsonSimpleSerializer(object):
    def loads(self, response):
        try:
            return json.loads(response.content)
        except (UnicodeDecodeError, ValueError):
            return {"errors": response.content}

    def loads_errors(self, response):
        try:
            return json.loads(response.text).get("errors")
        except (UnicodeDecodeError, ValueError):
            return {"errors": response.content}


class CommandBaseBackend(object):
    def get_session(self):
        return self.session

    def get_base_url(self):
        return ""

    def get_serializer(self):
        return JsonSimpleSerializer()
