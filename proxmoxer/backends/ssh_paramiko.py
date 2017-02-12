__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2017'
__licence__ = 'MIT'


import os
from proxmoxer.backends.base_ssh import ProxmoxBaseSSHSession, BaseBackend

try:
    import paramiko
except ImportError:
    import sys
    sys.stderr.write("Chosen backend requires 'paramiko' module\n")
    sys.exit(1)


class ProxmoxParamikoSession(ProxmoxBaseSSHSession):
    def __init__(self, host,
                 username,
                 password=None,
                 private_key_file=None,
                 port=22,
                 timeout=5,
                 sudo=False):
        self.host = host
        self.username = username
        self.password = password
        self.private_key_file = private_key_file
        self.port = port
        self.timeout = timeout
        self.sudo = sudo
        self.ssh_client = self._connect()

    def _connect(self):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.private_key_file:
            key_filename = os.path.expanduser(self.private_key_file)
        else:
            key_filename = None

        ssh_client.connect(self.host,
                           username=self.username,
                           allow_agent=(not self.password),
                           look_for_keys=True,
                           key_filename=key_filename,
                           password=self.password,
                           timeout=self.timeout,
                           port=self.port)

        return ssh_client

    def _exec(self, cmd):
        if self.sudo:
            cmd = 'sudo ' + cmd
        session = self.ssh_client.get_transport().open_session()
        session.exec_command(cmd)
        stdout = ''.join(session.makefile('rb', -1))
        stderr = ''.join(session.makefile_stderr('rb', -1))
        return stdout, stderr

    def upload_file_obj(self, file_obj, remote_path):
        sftp = self.ssh_client.open_sftp()
        sftp.putfo(file_obj, remote_path)
        sftp.close()


class Backend(BaseBackend):
    def __init__(self, host, user, password=None, private_key_file=None, port=22, timeout=5, sudo=False):
        self.session = ProxmoxParamikoSession(host, user,
                                              password=password,
                                              private_key_file=private_key_file,
                                              port=port,
                                              timeout=timeout,
                                              sudo=sudo)


