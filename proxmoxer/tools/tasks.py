__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2022"
__license__ = "MIT"

import time


class Tasks:
    """
    Ease-of-use tools for interacting with the tasks endpoints
    in the Proxmox API.
    """

    @staticmethod
    def blocking_status(prox, task_id, timeout=300, polling_interval=1):
        """
        Turns getting the status of a Proxmox task into a blocking call
        by polling the API until the task completes

        :param prox: The Proxmox object used to query for status
        :type prox: ProxmoxAPI
        :param task_id: the UPID of the task
        :type task_id: str
        :param timeout: If the task does not complete in this time (in seconds) return None, defaults to 300
        :type timeout: int, optional
        :param polling_interval: the time to wait between checking for status updates, defaults to 1
        :type polling_interval: float, optional
        :return: the status of the task
        :rtype: dict
        """
        node: str = Tasks.decode_upid(task_id)["node"]
        start_time: float = time.monotonic()
        data = {"status": ""}
        while data["status"] != "stopped":
            data = prox.nodes(node).tasks(task_id).status.get()
            if start_time + timeout <= time.monotonic():
                data = None  # type: ignore
                break

            time.sleep(polling_interval)
        return data

    @staticmethod
    def decode_upid(upid):
        """
        Decodes the sections of a UPID into separate fields

        :param upid: a UPID string
        :type upid: str
        :return: The decoded information from the UPID
        :rtype: dict
        """
        segments = upid.split(":")
        if segments[0] != "UPID" or len(segments) != 9:
            raise AssertionError("UPID is not in the correct format")

        data = {
            "upid": upid,
            "node": segments[1],
            "pid": int(segments[2], 16),
            "pstart": int(segments[3], 16),
            "starttime": int(segments[4], 16),
            "type": segments[5],
            "id": segments[6],
            "user": segments[7].split("!")[0],
            "comment": segments[8],
        }
        return data

    @staticmethod
    def decode_log(log_list):
        """
        Takes in a task's log data and returns a multiline string representation

        :param log_list: The log formatting returned by the Proxmox API
        :type log_list: list of dicts
        :return: a multiline string of the log
        :rtype: str
        """
        str_list = [""] * len(log_list)
        for line in log_list:
            str_list[line["n"] - 1] = line.get("t", "")

        return "\n".join(str_list)
