__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2023"
__license__ = "MIT"

import hashlib
import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

from proxmoxer import ProxmoxResource, ResourceException
from proxmoxer.tools.tasks import Tasks

CHECKSUM_CHUNK_SIZE = 16384  # read 16k at a time while calculating the checksum for upload

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.WARNING)

try:
    import requests
except ImportError:
    logger.error("Files tools requires 'requests' module\n")
    sys.exit(1)


class ChecksumInfo:
    def __init__(self, name: str, hex_size: int):
        self.name = name
        self.hex_size = hex_size

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.name} ({self.hex_size} digits)"


class SupportedChecksums(Enum):
    """
    An Enum of the checksum types supported by Proxmox
    """

    # ordered by preference for longer/stronger checksums first
    SHA512 = ChecksumInfo("sha512", 128)
    SHA256 = ChecksumInfo("sha256", 64)
    SHA224 = ChecksumInfo("sha224", 56)
    SHA384 = ChecksumInfo("sha384", 96)
    MD5 = ChecksumInfo("md5", 32)
    SHA1 = ChecksumInfo("sha1", 40)


class Files:
    """
    Ease-of-use tools for interacting with the uploading/downloading files
    in Proxmox VE
    """

    def __init__(self, prox: ProxmoxResource, node: str, storage: str):
        self._prox = prox
        self._node = node
        self._storage = storage

    def __repr__(self):
        return f"Files ({self._node}/{self._storage} at {self._prox})"

    def upload_local_file_to_storage(
        self,
        filename: str,
        do_checksum_check: bool = True,
        blocking_status: bool = True,
    ):
        file_path = Path(filename)

        if not file_path.is_file():
            logger.error(f'"{file_path.absolute()}" does not exist or is not a file')
            return None

        # init to None in case errors cause no values to be set
        upid: str = ""
        checksum: str = None
        checksum_type: str = None

        try:
            with open(file_path.absolute(), "rb") as f_obj:
                if do_checksum_check:
                    # iterate through SupportedChecksums and find the first one in hashlib.algorithms_available
                    for checksum_info in (v.value for v in SupportedChecksums):
                        if checksum_info.name in hashlib.algorithms_available:
                            checksum_type = checksum_info.name
                            break

                    if checksum_type is None:
                        logger.warning(
                            "There are no Proxmox supported checksums which are supported by hashlib. Skipping checksum validation"
                        )
                    else:
                        h = hashlib.new(checksum_type)

                        # Iterate through the file in CHECKSUM_CHUNK_SIZE size
                        for byte_block in iter(lambda: f_obj.read(CHECKSUM_CHUNK_SIZE), b""):
                            h.update(byte_block)
                        checksum = h.hexdigest()
                        logger.debug(
                            f"The {checksum_type} checksum of {file_path.absolute()} is {checksum}"
                        )

                        # reset to the start of the file so the upload can use the same file handle
                        f_obj.seek(0)

                params = {
                    "content": "iso" if file_path.absolute().name.endswith("iso") else "vztmpl",
                    "checksum-algorithm": checksum_type,
                    "checksum": checksum,
                    "filename": f_obj,
                }
                upid = self._prox.nodes(self._node).storage(self._storage).upload.post(**params)
        except OSError as e:
            logger.error(e)
            return None

        if blocking_status:
            return Tasks.blocking_status(self._prox, upid)
        else:
            return self._prox.nodes(self._node).tasks(upid).status.get()

    def download_file_to_storage(
        self,
        url: str,
        checksum: Optional[str] = None,
        checksum_type: Optional[str] = None,
        blocking_status: bool = True,
    ):
        file_info = self.get_file_info(url)
        filename = None

        if file_info is not None:
            filename = file_info.get("filename")

        if checksum is None and checksum_type is None:
            checksum, checksum_info = self.get_checksums_from_file_url(url, filename)
            checksum_type = checksum_info.name if checksum_info else None
        elif checksum is None or checksum_type is None:
            logger.error(
                "Must pass both checksum and checksum_type or leave both None for auto-discovery"
            )
            return None

        if checksum is None or checksum_type is None:
            logger.warning("Unable to discover checksum. Will not do checksum validation")

        params = {
            "checksum-algorithm": checksum_type,
            "url": url,
            "checksum": checksum,
            "content": "iso" if url.endswith("iso") else "vztmpl",
            "filename": filename,
        }
        upid = self._prox.nodes(self._node).storage(self._storage)("download-url").post(**params)

        if blocking_status:
            return Tasks.blocking_status(self._prox, upid)
        else:
            return self._prox.nodes(self._node).tasks(upid).status.get()

    def get_file_info(self, url: str):
        try:
            return self._prox.nodes(self._node)("query-url-metadata").get(url=url)

        except ResourceException as e:
            logger.warning(f"Unable to get information for {url}: {e}")
            return None

    @staticmethod
    def get_checksums_from_file_url(
        url: str, filename: str = None, preferred_type=SupportedChecksums.SHA512.value
    ):
        getters_by_quality = [
            Files._get_checksum_from_sibling_file,
            Files._get_checksum_from_extension,
            Files._get_checksum_from_extension_upper,
        ]

        # hacky way to try the preferred_type first while still trying all types with no duplicates
        all_types_with_priority = list(
            dict.fromkeys([preferred_type, *(map(lambda t: t.value, SupportedChecksums))])
        )
        for c_info in all_types_with_priority:
            for getter in getters_by_quality:
                checksum: str = getter(url, c_info, filename)
                if checksum is not None:
                    logger.info(f"{getter} found {str(c_info)} checksum {checksum}")
                    return (checksum, c_info)
                else:
                    logger.debug(f"{getter} found no {str(c_info)} checksum")

        return (None, None)

    @staticmethod
    def _get_checksum_from_sibling_file(
        url: str, checksum_info: ChecksumInfo, filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Uses a checksum file in the same path as the target file to discover the checksum

        :param url: the URL string of the target file
        :type url: str
        :param checksum_info: the type of checksum to search for
        :type checksum_info: ChecksumInfo
        :param filename: the filename to use for finding the checksum. If None, it will be discovered from the url
        :type filename: str | None
        :return: a string of the checksum if found, else None
        :rtype: str | None
        """
        sumfile_url = urljoin(url, (checksum_info.name + "SUMS").upper())
        filename = filename or os.path.basename(urlparse(url).path)

        return Files._get_checksum_helper(sumfile_url, filename, checksum_info)

    @staticmethod
    def _get_checksum_from_extension(
        url: str, checksum_info: ChecksumInfo, filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Uses a checksum file with a checksum extension added to the target file to discover the checksum

        :param url: the URL string of the target file
        :type url: str
        :param checksum_info: the type of checksum to search for
        :type checksum_info: ChecksumInfo
        :param filename: the filename to use for finding the checksum. If None, it will be discovered from the url
        :type filename: str | None
        :return: a string of the checksum if found, else None
        :rtype: str | None
        """
        sumfile_url = url + "." + checksum_info.name
        filename = filename or os.path.basename(urlparse(url).path)

        return Files._get_checksum_helper(sumfile_url, filename, checksum_info)

    @staticmethod
    def _get_checksum_from_extension_upper(
        url: str, checksum_info: ChecksumInfo, filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Uses a checksum file with a checksum extension added to the target file to discover the checksum

        :param url: the URL string of the target file
        :type url: str
        :param checksum_info: the type of checksum to search for
        :type checksum_info: ChecksumInfo
        :param filename: the filename to use for finding the checksum. If None, it will be discovered from the url
        :type filename: str | None
        :return: a string of the checksum if found, else None
        :rtype: str | None
        """
        sumfile_url = url + "." + checksum_info.name.upper()
        filename = filename or os.path.basename(urlparse(url).path)

        return Files._get_checksum_helper(sumfile_url, filename, checksum_info)

    @staticmethod
    def _get_checksum_helper(sumfile_url: str, filename: str, checksum_info: ChecksumInfo):
        logger.debug(f"getting {sumfile_url}")
        try:
            resp = requests.get(sumfile_url, timeout=10)
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            logger.info(f"Failed when trying to get {sumfile_url}")
            return None

        if resp.status_code == 200:
            for line in resp.iter_lines():
                line_str = line.decode("utf-8")
                logger.debug(f"checking for '{filename}' in '{line_str}'")
                if filename in str(line_str):
                    return line_str[0 : checksum_info.hex_size]
        return None
