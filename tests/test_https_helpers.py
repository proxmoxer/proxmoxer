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


class TestMergeDicts:
    """
    Tests for the merge_dicts() function within proxmoxer.backends.https
    """

    def test_empty(self):
        a = {}
        b = {}
        c = https.merge_dicts(a, b)
        assert c == {}

    def test_simple(self):
        a = {"a": 1}
        b = {"b": 2}
        c = https.merge_dicts(a, b)
        assert c == {"a": 1, "b": 2}

    def test_unordered(self):
        a = {"a": 1}
        b = {"b": 2}
        c = https.merge_dicts(b, a)
        assert c == {"a": 1, "b": 2}

    def test_duplicate(self):
        a = {"value": "a"}
        b = {"value": "b"}
        c = https.merge_dicts(a, b)
        assert c == {"value": "b"}

    def test_duplicate_reverse_order(self):
        a = {"value": "a"}
        b = {"value": "b"}
        c = https.merge_dicts(b, a)
        assert c == {"value": "a"}

    def test_duplicate_deep(self):
        a = {"value": {"deep": "a"}, "a": 1}
        b = {"value": {"deep": "b"}, "b": 2}
        c = https.merge_dicts(a, b)
        assert c == {"value": {"deep": "b"}, "a": 1, "b": 2}
