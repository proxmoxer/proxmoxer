__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2022"
__license__ = "MIT"

import tempfile

from proxmoxer.backends import https


class TestGetFileSize:
    """
    Tests for the get_file_size() function within proxmoxer.backends.https
    """

    def test_empty(self):
        with tempfile.TemporaryFile("w+b") as f_obj:
            assert https.get_file_size(f_obj) == 0

    def test_small(self):
        size = 100
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            assert https.get_file_size(f_obj) == size

    def test_large(self):
        size = 10 * 1024 * 1024  # 10 MB
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            assert https.get_file_size(f_obj) == size

    def test_half_seek(self):
        size = 200
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(int(size / 2))
            assert https.get_file_size(f_obj) == size

    def test_full_seek(self):
        size = 200
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(size)
            assert https.get_file_size(f_obj) == size


class TestGetFileSizePartial:
    """
    Tests for the get_file_size_partial() function within proxmoxer.backends.https
    """

    def test_empty(self):
        with tempfile.TemporaryFile("w+b") as f_obj:
            assert https.get_file_size_partial(f_obj) == 0

    def test_small(self):
        size = 100
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(0)
            assert https.get_file_size_partial(f_obj) == size

    def test_large(self):
        size = 10 * 1024 * 1024  # 10 MB
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(0)
            assert https.get_file_size_partial(f_obj) == size

    def test_half_seek(self):
        size = 200
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(int(size / 2))
            assert https.get_file_size_partial(f_obj) == size / 2

    def test_full_seek(self):
        size = 200
        with tempfile.TemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * size)
            f_obj.seek(size)
            assert https.get_file_size_partial(f_obj) == 0
