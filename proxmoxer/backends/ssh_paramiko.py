from itertools import chain
import json
import os
import paramiko


class Response(object):
    def __init__(self, content, status_code):
        self.status_code = status_code
        self.content = content
        self.headers = {"content-type": "application/json"}


class ProxmoxParamikoSession(object):
    def __init__(self, host,
                 username,
                 password=None,
                 private_key_file=None,
                 port=22,
                 timeout=5):
        self.host = host
        self.username = username
        self.password = password
        self.private_key_file = private_key_file
        self.port = port
        self.timeout = timeout
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
        print cmd
        session = self.ssh_client.get_transport().open_session()

        session.exec_command(cmd)

        size = 4096
        stdout = ''.join(session.makefile('rb', size))
        stderr = ''.join(session.makefile_stderr('rb', size))
        return stdout, stderr

    # noinspection PyUnusedLocal
    def request(self, method, url, data=None, params=None, headers=None):
        method = method.lower()
        data = data or {}
        params = params or {}

        cmd = {'post': 'create',
               'put': 'set'}.get(method, method)

        #for 'upload' call some workaround
        tmp_filename = ''
        if url.endswith('upload'):
            #copy file to temporary location on proxmox host
            tmp_filename, _ = self._exec(
                "python -c 'import tempfile; tf = tempfile.NamedTemporaryFile(); print tf.name'")
            self.upload_file_obj(data['filename'], tmp_filename)
            data['filename'] = data['filename'].name
            data['tmpfilename'] = tmp_filename

        translated_data = ' '.join(["-{0} {1}".format(k, v) for k, v in chain(data.iteritems(), params.iteritems())])
        full_cmd = 'pvesh {0} {1} {2}'.format(cmd, url, translated_data)

        stdout, stderr = self._exec(full_cmd)
        return Response(stdout, int(stderr.split()[0]))

    def upload_file_obj(self, file_obj, remote_path):
        sftp = self.ssh_client.open_sftp()
        remote_file = sftp.open(remote_path, 'wb')
        remote_file.write(file_obj.read())
        remote_file.close()


class JsonSimpleSerializer(object):

    def loads(self, response):
        try:
            return json.loads(response.content)
        except ValueError:
            return response.content


class Backend(object):
    def __init__(self, host, user, password=None, private_key_file=None, port=22):
        self.session = ProxmoxParamikoSession(host, user, password, private_key_file, port)

    def get_session(self):
        return self.session

    def get_base_url(self):
        return ''

    def get_serializer(self):
        return JsonSimpleSerializer()

