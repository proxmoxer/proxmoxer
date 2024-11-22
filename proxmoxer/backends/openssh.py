__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"

import logging

from proxmoxer.backends.command_base import (
    CommandBaseBackend,
    CommandBaseSession,
    shell_join,
)

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)

try:
    import openssh_wrapper
except ImportError:
    import sys

    logger.error("Chosen backend requires 'openssh_wrapper' module\n")
    sys.exit(1)


class OpenSSHSession(CommandBaseSession):
    def __init__(
        self,
        host,
        user,
        config_file=None,
        port=22,
        identity_file=None,
        forward_ssh_agent=False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.host = host
        self.user = user
        self.config_file = config_file
        self.port = port
        self.forward_ssh_agent = forward_ssh_agent
        self.identity_file = identity_file

        self.ssh_client = self._connect()

    def _connect(self):
        return openssh_wrapper.SSHConnection(
            self.host,
            login=self.user,
            port=str(self.port),  # openssh_wrapper complains if this is an int
            configfile=self.config_file,
            identity_file=self.identity_file,
            timeout=self.timeout,
        )

    def _exec(self, cmd):
        ret = self.ssh_client.run(shell_join(cmd), forward_ssh_agent=self.forward_ssh_agent)
        return ret.stdout, ret.stderr

    def upload_file_obj(self, file_obj, remote_path):
        self.ssh_client.scp((file_obj,), target=remote_path)


class Backend(CommandBaseBackend):
    def __init__(self, *args, **kwargs):
        self.session = OpenSSHSession(*args, **kwargs)
        self.target = self.session.host
