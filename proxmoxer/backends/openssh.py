__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2015'
__licence__ = 'MIT'


from proxmoxer.backends.base_ssh import ProxmoxBaseSSHSession, BaseBackend

try:
    import openssh_wrapper
except ImportError:
    import sys
    sys.stderr.write("Chosen backend requires 'openssh_wrapper' module\n")
    sys.exit(1)


class ProxmoxOpenSSHSession(ProxmoxBaseSSHSession):
    def __init__(self, host,
                 username,
                 configfile=None,
                 port=22,
                 timeout=5,
                 forward_ssh_agent=False):
        self.host = host
        self.username = username
        self.configfile = configfile
        self.port = port
        self.timeout = timeout
        self.forward_ssh_agent = forward_ssh_agent
        self.ssh_client = openssh_wrapper.SSHConnection(self.host,
                                                        login=self.username,
                                                        port=self.port,
                                                        timeout=self.timeout)

    def _exec(self, cmd):
        ret = self.ssh_client.run(cmd, forward_ssh_agent=self.forward_ssh_agent)
        return ret.stdout, ret.stderr

    def upload_file_obj(self, file_obj, remote_path):
        self.ssh_client.scp((file_obj,), target=remote_path)


class Backend(BaseBackend):
    def __init__(self, host, user, configfile=None, port=22, timeout=5, forward_ssh_agent=False):
        self.session = ProxmoxOpenSSHSession(host, user,
                                             configfile=configfile,
                                             port=port,
                                             timeout=timeout,
                                             forward_ssh_agent=forward_ssh_agent)
