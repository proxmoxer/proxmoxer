__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2023"
__license__ = "MIT"

import logging

from proxmoxer import ProxmoxAPI
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

        # this is the default "stopped" task mock information
        assert status == {
            "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:stopped",
            "starttime": 1661825068,
            "user": "root@pam",
            "type": "vzdump",
            "pstart": 284768076,
            "status": "stopped",
            "exitstatus": "interrupted by signal",
            "pid": 1044989,
            "id": "110",
            "node": "node1",
        }
        assert caplog.record_tuples == []

    def test_download_no_blocking(self, mock_files_and_pve, caplog):
        status = self.f.download_file_to_storage(
            "https://sub.domain.tld/checksums/file.iso", blocking_status=False
        )

        # this is the default "stopped" task mock information
        assert status == {
            "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:stopped",
            "starttime": 1661825068,
            "user": "root@pam",
            "type": "vzdump",
            "pstart": 284768076,
            "status": "stopped",
            "exitstatus": "interrupted by signal",
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
            "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:stopped",
            "starttime": 1661825068,
            "user": "root@pam",
            "type": "vzdump",
            "pstart": 284768076,
            "status": "stopped",
            "exitstatus": "interrupted by signal",
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
