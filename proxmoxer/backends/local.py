import shutil
from subprocess import PIPE, Popen

from proxmoxer.backends.base import BaseBackend, BaseSession


class LocalSession(BaseSession):
    def _exec(self, cmd):
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate(timeout=self.timeout)
        return stdout.decode(), stderr.decode()

    def upload_file_obj(self, file_obj, remote_path):
        with open(remote_path, "wb") as fp:
            shutil.copyfileobj(file_obj, fp)


class Backend(BaseBackend):
    def __init__(self, *args, **kwargs):
        self.session = LocalSession(*args, **kwargs)
