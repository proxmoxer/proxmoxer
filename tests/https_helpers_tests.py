import tempfile

from nose.tools import eq_

from proxmoxer.backends import https


def test_get_file_size_empty():
    with tempfile.TemporaryFile("w+b") as f_obj:
        eq_(https.get_file_size(f_obj), 0)


def test_get_file_size_small():
    size = 100
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        eq_(https.get_file_size(f_obj), size)


def test_get_file_size_large():
    size = 10 * 1024 * 1024  # 10 MB
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        eq_(https.get_file_size(f_obj), size)


def test_get_file_size_half_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(int(size / 2))
        eq_(https.get_file_size(f_obj), size)


def test_get_file_size_full_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(size)
        eq_(https.get_file_size(f_obj), size)


def test_get_file_size_partial_half_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(int(size / 2))
        eq_(https.get_file_size_partial(f_obj), size / 2)


def test_get_file_size_partial_full_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(size)
        eq_(https.get_file_size_partial(f_obj), 0)


def test_get_file_size_partial_no_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(0)
        eq_(https.get_file_size_partial(f_obj), size)


def test_merge_dicts_empty():
    a = {}
    b = {}
    c = https.merge_dicts(a, b)
    eq_(c, {})


def test_merge_dicts_simple():
    a = {"a": 1}
    b = {"b": 2}
    c = https.merge_dicts(a, b)
    eq_(c, {"a": 1, "b": 2})


def test_merge_dicts_unordered():
    a = {"a": 1}
    b = {"b": 2}
    c = https.merge_dicts(b, a)
    eq_(c, {"a": 1, "b": 2})


def test_merge_dicts_duplicate():
    a = {"value": "a"}
    b = {"value": "b"}
    c = https.merge_dicts(a, b)
    eq_(c, {"value": "b"})


def test_merge_dicts_duplicate_reverse_order():
    a = {"value": "a"}
    b = {"value": "b"}
    c = https.merge_dicts(b, a)
    eq_(c, {"value": "a"})


def test_merge_dicts_duplicate_deep():
    a = {"value": {"deep": "a"}, "a": 1}
    b = {"value": {"deep": "b"}, "b": 2}
    c = https.merge_dicts(a, b)
    eq_(c, {"value": {"deep": "b"}, "a": 1, "b": 2})
