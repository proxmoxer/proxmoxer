__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2022"
__license__ = "MIT"

import logging

import pytest

from proxmoxer import ProxmoxAPI
from proxmoxer.tools import Tasks

from ..api_mock import mock_pve  # pylint: disable=unused-import # noqa: F401


class TestBlockingStatus:
    def test_basic(self, mocked_prox, caplog):
        caplog.set_level(logging.DEBUG, logger="proxmoxer.core")

        status = Tasks.blocking_status(
            mocked_prox, "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:done"
        )

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
                "proxmoxer.core",
                20,
                "GET https://1.2.3.4:1234/api2/json/nodes/node1/tasks/UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:done/status",
            ),
            (
                "proxmoxer.core",
                10,
                'Status code: 200, output: b\'{"data": {"upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:done", "starttime": 1661825068, "user": "root@pam", "type": "vzdump", "pstart": 284768076, "status": "stopped", "exitstatus": "OK", "pid": 1044989, "id": "110", "node": "node1"}}\'',
            ),
        ]

    def test_zeroed(self, mocked_prox, caplog):
        caplog.set_level(logging.DEBUG, logger="proxmoxer.core")

        status = Tasks.blocking_status(
            mocked_prox, "UPID:node:00000000:00000000:00000000:task:id:root@pam:comment"
        )

        assert status == {
            "upid": "UPID:node:00000000:00000000:00000000:task:id:root@pam:comment",
            "node": "node",
            "pid": 0,
            "pstart": 0,
            "starttime": 0,
            "type": "task",
            "id": "id",
            "user": "root@pam",
            "status": "stopped",
            "exitstatus": "OK",
        }
        assert caplog.record_tuples == [
            (
                "proxmoxer.core",
                20,
                "GET https://1.2.3.4:1234/api2/json/nodes/node/tasks/UPID:node:00000000:00000000:00000000:task:id:root@pam:comment/status",
            ),
            (
                "proxmoxer.core",
                10,
                'Status code: 200, output: b\'{"data": {"upid": "UPID:node:00000000:00000000:00000000:task:id:root@pam:comment", "node": "node", "pid": 0, "pstart": 0, "starttime": 0, "type": "task", "id": "id", "user": "root@pam", "status": "stopped", "exitstatus": "OK"}}\'',
            ),
        ]

    def test_killed(self, mocked_prox, caplog):
        caplog.set_level(logging.DEBUG, logger="proxmoxer.core")

        status = Tasks.blocking_status(
            mocked_prox, "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:stopped"
        )

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
                "proxmoxer.core",
                20,
                "GET https://1.2.3.4:1234/api2/json/nodes/node1/tasks/UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:stopped/status",
            ),
            (
                "proxmoxer.core",
                10,
                'Status code: 200, output: b\'{"data": {"upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:stopped", "starttime": 1661825068, "user": "root@pam", "type": "vzdump", "pstart": 284768076, "status": "stopped", "exitstatus": "interrupted by signal", "pid": 1044989, "id": "110", "node": "node1"}}\'',
            ),
        ]

    def test_timeout(self, mocked_prox, caplog):
        caplog.set_level(logging.DEBUG, logger="proxmoxer.core")

        status = Tasks.blocking_status(
            mocked_prox,
            "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running",
            0.021,
            0.01,
        )

        assert status is None
        assert caplog.record_tuples == [
            (
                "proxmoxer.core",
                20,
                "GET https://1.2.3.4:1234/api2/json/nodes/node1/tasks/UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running/status",
            ),
            (
                "proxmoxer.core",
                10,
                'Status code: 200, output: b\'{"data": {"id": "110", "pid": 1044989, "node": "node1", "pstart": 284768076, "status": "running", "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running", "starttime": 1661825068, "user": "root@pam", "type": "vzdump"}}\'',
            ),
            (
                "proxmoxer.core",
                20,
                "GET https://1.2.3.4:1234/api2/json/nodes/node1/tasks/UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running/status",
            ),
            (
                "proxmoxer.core",
                10,
                'Status code: 200, output: b\'{"data": {"id": "110", "pid": 1044989, "node": "node1", "pstart": 284768076, "status": "running", "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running", "starttime": 1661825068, "user": "root@pam", "type": "vzdump"}}\'',
            ),
            (
                "proxmoxer.core",
                20,
                "GET https://1.2.3.4:1234/api2/json/nodes/node1/tasks/UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running/status",
            ),
            (
                "proxmoxer.core",
                10,
                'Status code: 200, output: b\'{"data": {"id": "110", "pid": 1044989, "node": "node1", "pstart": 284768076, "status": "running", "upid": "UPID:node1:000FF1FD:10F9374C:630D702C:vzdump:110:root@pam:keep-running", "starttime": 1661825068, "user": "root@pam", "type": "vzdump"}}\'',
            ),
        ]


class TestDecodeUpid:
    def test_basic(self):
        upid = "UPID:node:000CFC5C:03E8D0C3:6194806C:aptupdate::root@pam:"
        decoded = Tasks.decode_upid(upid)

        assert decoded["upid"] == upid
        assert decoded["node"] == "node"
        assert decoded["pid"] == 851036
        assert decoded["pstart"] == 65589443
        assert decoded["starttime"] == 1637122156
        assert decoded["type"] == "aptupdate"
        assert decoded["id"] == ""
        assert decoded["user"] == "root@pam"
        assert decoded["comment"] == ""

    def test_all_values(self):
        upid = "UPID:node1:000CFFFA:03E8EF53:619480BA:vzdump:103:root@pam:local"
        decoded = Tasks.decode_upid(upid)

        assert decoded["upid"] == upid
        assert decoded["node"] == "node1"
        assert decoded["pid"] == 851962
        assert decoded["pstart"] == 65597267
        assert decoded["starttime"] == 1637122234
        assert decoded["type"] == "vzdump"
        assert decoded["id"] == "103"
        assert decoded["user"] == "root@pam"
        assert decoded["comment"] == "local"

    def test_invalid_length(self):
        upid = "UPID:node1:000CFFFA:03E8EF53:619480BA:vzdump:103:root@pam"
        with pytest.raises(AssertionError) as exc_info:
            Tasks.decode_upid(upid)

        assert str(exc_info.value) == "UPID is not in the correct format"

    def test_invalid_start(self):
        upid = "ASDF:node1:000CFFFA:03E8EF53:619480BA:vzdump:103:root@pam:"
        with pytest.raises(AssertionError) as exc_info:
            Tasks.decode_upid(upid)

        assert str(exc_info.value) == "UPID is not in the correct format"


class TestDecodeLog:
    def test_basic(self):
        log_list = [{"n": 1, "t": "client connection: 127.0.0.1:49608"}, {"t": "TASK OK", "n": 2}]
        log_str = Tasks.decode_log(log_list)

        assert log_str == "client connection: 127.0.0.1:49608\nTASK OK"

    def test_empty(self):
        log_list = []
        log_str = Tasks.decode_log(log_list)

        assert log_str == ""

    def test_unordered(self):
        log_list = [{"n": 3, "t": "third"}, {"t": "first", "n": 1}, {"t": "second", "n": 2}]
        log_str = Tasks.decode_log(log_list)

        assert log_str == "first\nsecond\nthird"


@pytest.fixture
def mocked_prox(mock_pve):
    return ProxmoxAPI("1.2.3.4:1234", user="user", password="password")
