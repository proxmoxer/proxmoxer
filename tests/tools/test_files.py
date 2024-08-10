__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2023"
__license__ = "MIT"

import logging
import tempfile
from unittest import mock

import pytest

from proxmoxer import ProxmoxAPI, core
from proxmoxer.tools import ChecksumInfo, Files, SupportedChecksums

from ..api_mock import mock_pve  # pylint: disable=unused-import # noqa: F401
from ..files_mock import (  # pylint: disable=unused-import # noqa: F401
    mock_files,
    mock_files_and_pve,
)

MODULE_LOGGER_NAME = "proxmoxer.tools.files"


class TestChecksumInfo:
    def test_basic(self):
        info = ChecksumInfo("name", 123)

        assert info.name == "name"
        assert info.hex_size == 123

    def test_str(self):
        info = ChecksumInfo("name", 123)

        assert str(info) == "name"

    def test_repr(self):
        info = ChecksumInfo("name", 123)

        assert repr(info) == "name (123 digits)"


class TestGetChecksum:
    def test_get_checksum_from_sibling_file_success(self, mock_files):
        url = "https://sub.domain.tld/sibling/file.iso"
        exp_hash = "this_is_the_hash"
        info = ChecksumInfo("testing", 16)
        res1 = Files._get_checksum_from_sibling_file(url, checksum_info=info)
        res2 = Files._get_checksum_from_sibling_file(url, checksum_info=info, filename="file.iso")

        assert res1 == exp_hash
        assert res2 == exp_hash

    def test_get_checksum_from_sibling_file_fail(self, mock_files):
        url = "https://sub.domain.tld/sibling/missing.iso"
        info = ChecksumInfo("testing", 16)
        res1 = Files._get_checksum_from_sibling_file(url, checksum_info=info)
        res2 = Files._get_checksum_from_sibling_file(
            url, checksum_info=info, filename="missing.iso"
        )

        assert res1 is None
        assert res2 is None

    def test_get_checksum_from_extension_success(self, mock_files):
        url = "https://sub.domain.tld/extension/file.iso"
        exp_hash = "this_is_the_hash"
        info = ChecksumInfo("testing", 16)
        res1 = Files._get_checksum_from_extension(url, checksum_info=info)
        res2 = Files._get_checksum_from_extension(url, checksum_info=info, filename="file.iso")

        assert res1 == exp_hash
        assert res2 == exp_hash

    def test_get_checksum_from_extension_fail(self, mock_files):
        url = "https://sub.domain.tld/extension/missing.iso"

        info = ChecksumInfo("testing", 16)
        res1 = Files._get_checksum_from_extension(url, checksum_info=info)
        res2 = Files._get_checksum_from_extension(
            url, checksum_info=info, filename="connectionerror.iso"
        )
        res3 = Files._get_checksum_from_extension(
            url, checksum_info=info, filename="readtimeout.iso"
        )

        assert res1 is None
        assert res2 is None
        assert res3 is None

    def test_get_checksum_from_extension_upper_success(self, mock_files):
        url = "https://sub.domain.tld/upper/file.iso"
        exp_hash = "this_is_the_hash"
        info = ChecksumInfo("testing", 16)
        res1 = Files._get_checksum_from_extension_upper(url, checksum_info=info)
        res2 = Files._get_checksum_from_extension_upper(
            url, checksum_info=info, filename="file.iso"
        )

        assert res1 == exp_hash
        assert res2 == exp_hash

    def test_get_checksum_from_extension_upper_fail(self, mock_files):
        url = "https://sub.domain.tld/upper/missing.iso"
        info = ChecksumInfo("testing", 16)
        res1 = Files._get_checksum_from_extension_upper(url, checksum_info=info)
        res2 = Files._get_checksum_from_extension_upper(
            url, checksum_info=info, filename="missing.iso"
        )

        assert res1 is None
        assert res2 is None

    def test_get_checksums_from_file_url_all_checksums(self, mock_files):
        base_url = "https://sub.domain.tld/checksums/file.iso"
        full_checksum_string = "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890"
        for types_enum in SupportedChecksums:
            checksum_info = types_enum.value

            data = Files.get_checksums_from_file_url(base_url, preferred_type=checksum_info)

            assert data[0] == full_checksum_string[0 : checksum_info.hex_size]
            assert data[1] == checksum_info

    def test_get_checksums_from_file_url_missing(self, mock_files):
        url = "https://sub.domain.tld/missing.iso"

        data = Files.get_checksums_from_file_url(url)

        assert data[0] is None
        assert data[1] is None


class TestFiles:
    prox = ProxmoxAPI("1.2.3.4:1234", token_name="name", token_value="value")

    def test_init_basic(self):
        f = Files(self.prox, "node1", "storage1")

        assert f._prox == self.prox
        assert f._node == "node1"
        assert f._storage == "storage1"

    def test_repr(self):
        f = Files(self.prox, "node1", "storage1")
        assert (
            repr(f)
            == "Files (node1/storage1 at ProxmoxAPI (https backend for https://1.2.3.4:1234/api2/json))"
        )

    def test_get_file_info_pass(self, mock_pve):
        f = Files(self.prox, "node1", "storage1")
        info = f.get_file_info("https://sub.domain.tld/file.iso")

        assert info["filename"] == "file.iso"
        assert info["mimetype"] == "application/x-iso9660-image"
        assert info["size"] == 123456

    def test_get_file_info_fail(self, mock_pve):
        f = Files(self.prox, "node1", "storage1")
        info = f.get_file_info("https://sub.domain.tld/invalid.iso")

        assert info is None


class TestFilesDownload:
    prox = ProxmoxAPI("1.2.3.4:1234", token_name="name", token_value="value")
    f = Files(prox, "node1", "storage1")

    def test_download_discover_checksum(self, mock_files_and_pve, caplog):
        status = self.f.download_file_to_storage("https://sub.domain.tld/checksums/file.iso")

        # this is the default "done" task mock information
        assert status == {
            "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:done",
            "starttime": 1661825068,
            "user": "root@pam",
            "type": "vzdump",
            "pstart": 284768076,
            "status": "stopped",
            "exitstatus": "OK",
            "pid": 1044989,
            "id": "110",
            "node": "node1",
        }
        assert caplog.record_tuples == []

    def test_download_no_blocking(self, mock_files_and_pve, caplog):
        status = self.f.download_file_to_storage(
            "https://sub.domain.tld/checksums/file.iso", blocking_status=False
        )

        # this is the default "done" task mock information
        assert status == {
            "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:done",
            "starttime": 1661825068,
            "user": "root@pam",
            "type": "vzdump",
            "pstart": 284768076,
            "status": "stopped",
            "exitstatus": "OK",
            "pid": 1044989,
            "id": "110",
            "node": "node1",
        }
        assert caplog.record_tuples == []

    def test_download_no_discover_checksum(self, mock_files_and_pve, caplog):
        caplog.set_level(logging.WARNING, logger=MODULE_LOGGER_NAME)

        status = self.f.download_file_to_storage("https://sub.domain.tld/file.iso")

        # this is the default "stopped" task mock information
        assert status == {
            "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:done",
            "starttime": 1661825068,
            "user": "root@pam",
            "type": "vzdump",
            "pstart": 284768076,
            "status": "stopped",
            "exitstatus": "OK",
            "pid": 1044989,
            "id": "110",
            "node": "node1",
        }
        assert caplog.record_tuples == [
            (
                MODULE_LOGGER_NAME,
                logging.WARNING,
                "Unable to discover checksum. Will not do checksum validation",
            ),
        ]

    def test_uneven_checksum(self, caplog, mock_files_and_pve):
        caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
        status = self.f.download_file_to_storage("https://sub.domain.tld/file.iso", checksum="asdf")

        assert status is None

        assert caplog.record_tuples == [
            (
                MODULE_LOGGER_NAME,
                logging.ERROR,
                "Must pass both checksum and checksum_type or leave both None for auto-discovery",
            ),
        ]

    def test_uneven_checksum_type(self, caplog, mock_files_and_pve):
        caplog.set_level(logging.DEBUG, logger=MODULE_LOGGER_NAME)
        status = self.f.download_file_to_storage(
            "https://sub.domain.tld/file.iso", checksum_type="asdf"
        )

        assert status is None

        assert caplog.record_tuples == [
            (
                MODULE_LOGGER_NAME,
                logging.ERROR,
                "Must pass both checksum and checksum_type or leave both None for auto-discovery",
            ),
        ]

    def test_get_file_info_missing(self, mock_pve):
        f = Files(self.prox, "node1", "storage1")
        info = f.get_file_info("https://sub.domain.tld/missing.iso")

        assert info is None

    def test_get_file_info_non_iso(self, mock_pve):
        f = Files(self.prox, "node1", "storage1")
        info = f.get_file_info("https://sub.domain.tld/index.html")

        assert info["filename"] == "index.html"
        assert info["mimetype"] == "text/html"


class TestFilesUpload:
    prox = ProxmoxAPI("1.2.3.4:1234", token_name="name", token_value="value")
    f = Files(prox, "node1", "storage1")

    def test_upload_no_file(self, mock_files_and_pve, caplog):
        status = self.f.upload_local_file_to_storage("/does-not-exist.iso")

        assert status is None
        assert caplog.record_tuples == [
            (
                MODULE_LOGGER_NAME,
                logging.ERROR,
                '"/does-not-exist.iso" does not exist or is not a file',
            ),
        ]

    def test_upload_dir(self, mock_files_and_pve, caplog):
        with tempfile.TemporaryDirectory() as tmp_dir:
            status = self.f.upload_local_file_to_storage(tmp_dir)

            assert status is None
            assert caplog.record_tuples == [
                (
                    MODULE_LOGGER_NAME,
                    logging.ERROR,
                    f'"{tmp_dir}" does not exist or is not a file',
                ),
            ]

    def test_upload_empty_file(self, mock_files_and_pve, caplog):
        with tempfile.NamedTemporaryFile("rb") as f_obj:
            status = self.f.upload_local_file_to_storage(filename=f_obj.name)

            assert status is not None
            assert caplog.record_tuples == []

    def test_upload_non_empty_file(self, mock_files_and_pve, caplog):
        with tempfile.NamedTemporaryFile("w+b") as f_obj:
            f_obj.write(b"a" * 100)
            f_obj.seek(0)
            status = self.f.upload_local_file_to_storage(filename=f_obj.name)

            assert status is not None
            assert caplog.record_tuples == []

    def test_upload_no_checksum(self, mock_files_and_pve, caplog):
        with tempfile.NamedTemporaryFile("rb") as f_obj:
            status = self.f.upload_local_file_to_storage(
                filename=f_obj.name, do_checksum_check=False
            )

            assert status is not None
            assert caplog.record_tuples == []

    def test_upload_checksum_unavailable(self, mock_files_and_pve, caplog, apply_no_checksums):
        with tempfile.NamedTemporaryFile("rb") as f_obj:
            status = self.f.upload_local_file_to_storage(filename=f_obj.name)

            assert status is not None
            assert caplog.record_tuples == [
                (
                    MODULE_LOGGER_NAME,
                    logging.WARNING,
                    "There are no Proxmox supported checksums which are supported by hashlib. Skipping checksum validation",
                )
            ]

    def test_upload_non_blocking(self, mock_files_and_pve, caplog):
        with tempfile.NamedTemporaryFile("rb") as f_obj:
            status = self.f.upload_local_file_to_storage(filename=f_obj.name, blocking_status=False)

            assert status is not None
            assert caplog.record_tuples == []

    def test_upload_proxmox_error(self, mock_files_and_pve, caplog):
        with tempfile.NamedTemporaryFile("rb") as f_obj:
            f_copy = Files(self.f._prox, self.f._node, "missing")

            with pytest.raises(core.ResourceException) as exc_info:
                f_copy.upload_local_file_to_storage(filename=f_obj.name)

            assert exc_info.value.status_code == 500
            assert exc_info.value.status_message == "Internal Server Error"
            # assert exc_info.value.content == "storage 'missing' does not exist"

    def test_upload_io_error(self, mock_files_and_pve, caplog):
        with tempfile.NamedTemporaryFile("rb") as f_obj:
            mo = mock.mock_open()
            mo.side_effect = IOError("ERROR MESSAGE")
            with mock.patch("builtins.open", mo):
                status = self.f.upload_local_file_to_storage(filename=f_obj.name)

            assert status is None
            assert caplog.record_tuples == [(MODULE_LOGGER_NAME, logging.ERROR, "ERROR MESSAGE")]


@pytest.fixture
def apply_no_checksums():
    with mock.patch("hashlib.algorithms_available", set()):
        yield
