import tempfile

from proxmoxer.backends import local

# pylint: disable=no-self-use


class TestLocalBackend:
    def test_init(self):
        back = local.Backend()

        assert isinstance(back.session, local.LocalSession)


class TestLocalSession:

    _session = local.LocalSession()

    def test_upload_file_obj(self):
        size = 100

        with tempfile.NamedTemporaryFile("w+b") as f_obj, tempfile.NamedTemporaryFile(
            "rb"
        ) as dest_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(0)
            self._session.upload_file_obj(f_obj, dest_obj.name)

            # reset file cursor to start of file after copy
            f_obj.seek(0)

            assert f_obj.read() == dest_obj.read()

    def test_upload_file_obj_end(self):
        size = 100

        with tempfile.NamedTemporaryFile("w+b") as f_obj, tempfile.NamedTemporaryFile(
            "rb"
        ) as dest_obj:
            f_obj.write(b"a" * size)
            # do not seek to start of file before copy
            self._session.upload_file_obj(f_obj, dest_obj.name)

            assert b"" == dest_obj.read()

    def test_exec(self):
        cmd = [
            "python3",
            "-c",
            'import sys; sys.stdout.write("stdout content"); sys.stderr.write("stderr content")',
        ]

        stdout, stderr = self._session._exec(cmd)

        assert stdout == "stdout content"
        assert stderr == "stderr content"
