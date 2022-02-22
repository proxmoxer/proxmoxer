__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2017"
__license__ = "MIT"

from proxmoxer.backends.command_base import (
    CommandBaseBackend,
    CommandBaseSession,
    shelljoin,
)

try:
    import openssh_wrapper
except ImportError:
    import sys

    sys.stderr.write("Chosen backend requires 'openssh_wrapper' module\n")
    sys.exit(1)


class OpenSSHSession(CommandBaseSession):
    # formatting disabled due to python <= 3.5 syntax error with comma after **kwargs
    def __init__(
        self,
        host,
        user,
        configfile=None,
        port=22,
        forward_ssh_agent=False,
        identity_file=None,
        # fmt: off
        **kwargs
        # fmt: on
    ):
        super(OpenSSHSession, self).__init__(**kwargs)
        self.host = host
        self.user = user
        self.configfile = configfile
        self.port = port
        self.forward_ssh_agent = forward_ssh_agent
        self.identity_file = identity_file

        self.ssh_client = self._connect()

    def _connect(self):
        return openssh_wrapper.SSHConnection(
            self.host,
            login=self.user,
            port=self.port,
            timeout=self.timeout,
            identity_file=self.identity_file,
        )

    def _exec(self, cmd):
        ret = self.ssh_client.run(shelljoin(cmd), forward_ssh_agent=self.forward_ssh_agent)
        return ret.stdout, ret.stderr

    def upload_file_obj(self, file_obj, remote_path):
        self.ssh_client.scp((file_obj,), target=remote_path)


class Backend(CommandBaseBackend):
    def __init__(self, *args, **kwargs):
        self.session = OpenSSHSession(*args, **kwargs)
