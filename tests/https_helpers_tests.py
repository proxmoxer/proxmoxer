import tempfile

from nose.tools import assert_raises, eq_, ok_

from proxmoxer.backends import https


def test_getFileSize_empty():
    with tempfile.TemporaryFile("w+b") as f_obj:
        eq_(https.getFileSize(f_obj), 0)


def test_getFileSize_small():
    size = 100
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        eq_(https.getFileSize(f_obj), size)


def test_getFileSize_large():
    size = 10 * 1024 * 1024  # 10 MB
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        eq_(https.getFileSize(f_obj), size)


def test_getFileSize_half_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(int(size / 2))
        eq_(https.getFileSize(f_obj), size)


def test_getFileSize_full_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(size)
        eq_(https.getFileSize(f_obj), size)


def test_getFileSizePartial_half_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(int(size / 2))
        eq_(https.getFileSizePartial(f_obj), size / 2)


def test_getFileSizePartial_full_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(size)
        eq_(https.getFileSizePartial(f_obj), 0)


def test_getFileSizePartial_no_seek():
    size = 200
    with tempfile.TemporaryFile("w+b") as f_obj:
        f_obj.write(b"a" * size)
        f_obj.seek(0)
        eq_(https.getFileSizePartial(f_obj), size)


def test_mergeDicts_empty():
    a = {}
    b = {}
    c = https.mergeDicts(a, b)
    eq_(c, {})


def test_mergeDicts_simple():
    a = {"a": 1}
    b = {"b": 2}
    c = https.mergeDicts(a, b)
    eq_(c, {"a": 1, "b": 2})


def test_mergeDicts_unordered():
    a = {"a": 1}
    b = {"b": 2}
    c = https.mergeDicts(b, a)
    eq_(c, {"a": 1, "b": 2})


def test_mergeDicts_duplicate():
    a = {"value": "a"}
    b = {"value": "b"}
    c = https.mergeDicts(a, b)
    eq_(c, {"value": "b"})


def test_mergeDicts_duplicate_reverse_order():
    a = {"value": "a"}
    b = {"value": "b"}
    c = https.mergeDicts(b, a)
    eq_(c, {"value": "a"})


def test_mergeDicts_duplicate_deep():
    a = {"value": {"deep": "a"}, "a": 1}
    b = {"value": {"deep": "b"}, "b": 2}
    c = https.mergeDicts(a, b)
    eq_(c, {"value": {"deep": "b"}, "a": 1, "b": 2})
