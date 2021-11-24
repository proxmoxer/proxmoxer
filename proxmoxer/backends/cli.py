__author__ = 'Oleg Butovich'
__copyright__ = '(c) Oleg Butovich 2013-2017'
__licence__ = 'MIT'


from subprocess import Popen, PIPE, TimeoutExpired
import shlex, shutil
from proxmoxer.backends.base_ssh import ProxmoxBaseSSHSession, BaseBackend


class ProxmoxCliSession(ProxmoxBaseSSHSession):
    # Technically not an SSH session
    def __init__(self,
                 service='PVE',
                 timeout=5,
                 sudo=False):
        self.service = service.lower()
        self.timeout = timeout
        self.sudo = sudo

    def _exec(self, cmd):
        if self.sudo:
            cmd = 'sudo ' + cmd
        args = shlex.split(cmd)
        proc = Popen(args, stdout=PIPE, stderr=PIPE)
        try:
            stdout, stderr = proc.communicate(timeout=self.timeout)
        except TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        return stdout.decode(), stderr.decode()

    def upload_file_obj(self, file_obj, remote_path):
        with open(remote_path, 'wb') as fp:
            shutil.copyfileobj(file_obj, fp)


class Backend(BaseBackend):
    def __init__(self, _host=None, timeout=5, service='PVE', sudo=False):
        self.session = ProxmoxCliSession(service=service,
                                         timeout=timeout,
                                         sudo=sudo)

