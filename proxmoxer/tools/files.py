__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2023"
__license__ = "MIT"

import logging
import os
import sys
from enum import Enum
from typing import Optional
from urllib.parse import urljoin, urlparse

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

    SHA256 = ChecksumInfo("sha256", 64)
    MD5 = ChecksumInfo("md5", 32)
    SHA1 = ChecksumInfo("sha1", 40)
    SHA512 = ChecksumInfo("sha512", 128)
    SHA224 = ChecksumInfo("sha224", 56)
    SHA384 = ChecksumInfo("sha384", 96)


class Files:
    """
    Ease-of-use tools for interacting with the uploading/downloading files
    in Proxmox VE
    """

    @staticmethod
    def get_checksums_from_file_url(url: str, preferred_type=SupportedChecksums.SHA512):
        getters_by_quality = [
            Files._get_checksum_from_sibling_file,
            Files._get_checksum_from_extension,
            Files._get_checksum_from_extension_upper,
        ]

        # hacky way to try the preferred_type first while still trying all types with no duplicates
        all_types_with_priority = list(dict.fromkeys([preferred_type, *SupportedChecksums]))
        for c_type in all_types_with_priority:
            c_info = c_type.value  # get the ChecksumInfo out of the Enum
            for getter in getters_by_quality:
                checksum = getter(url, c_info)
                if checksum is not None:
                    logger.info(f"{getter} found {str(c_info)} checksum {checksum}")
                    return (checksum, c_info)
                else:
                    logger.debug(f"{getter} found no {str(c_info)} checksum")

        return (None, None)

    @staticmethod
    def _get_checksum_from_sibling_file(url: str, checksum_info: ChecksumInfo) -> Optional[str]:
        """
        Uses a checksum file in the same path as the target file to discover the checksum

        :param url: the URL string of the target file
        :type url: str
        :param checksum_info: the type of checksum to search for
        :type checksum_info: ChecksumInfo
        :return: a string of the checksum if found, else None
        :rtype: str | None
        """
        sumfile_url = urljoin(url, (checksum_info.name + "SUMS").upper())
        filename = os.path.basename(urlparse(url).path)

        return Files._get_checksum_helper(sumfile_url, filename, checksum_info)

    @staticmethod
    def _get_checksum_from_extension(url: str, checksum_info: ChecksumInfo) -> Optional[str]:
        """
        Uses a checksum file with a checksum extension added to the target file to discover the checksum

        :param url: the URL string of the target file
        :type url: str
        :param checksum_info: the type of checksum to search for
        :type checksum_info: ChecksumInfo
        :return: a string of the checksum if found, else None
        :rtype: str | None
        """
        sumfile_url = url + "." + checksum_info.name
        filename = os.path.basename(urlparse(url).path)

        return Files._get_checksum_helper(sumfile_url, filename, checksum_info)

    @staticmethod
    def _get_checksum_from_extension_upper(url: str, checksum_info: ChecksumInfo) -> Optional[str]:
        """
        Uses a checksum file with a checksum extension added to the target file to discover the checksum

        :param url: the URL string of the target file
        :type url: str
        :param checksum_info: the type of checksum to search for
        :type checksum_info: ChecksumInfo
        :return: a string of the checksum if found, else None
        :rtype: str | None
        """
        sumfile_url = url + "." + checksum_info.name.upper()
        filename = os.path.basename(urlparse(url).path)

        return Files._get_checksum_helper(sumfile_url, filename, checksum_info)

    @staticmethod
    def _get_checksum_helper(sumfile_url: str, filename: str, checksum_info: ChecksumInfo):
        logger.debug(f"getting {sumfile_url}")
        try:
            resp = requests.get(sumfile_url, timeout=10)
        except requests.exceptions.ReadTimeout as e:
            logger.warn(f"Failed when trying to get {sumfile_url}")
            raise e

        if resp.status_code == 200:
            for line in resp.iter_lines():
                line_str = line.decode("utf-8")
                logger.debug(f"checking for '{filename}' in '{line_str}'")
                if filename in str(line_str):
                    return line_str[0 : checksum_info.hex_size]
        return None