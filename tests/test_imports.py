import sys
from importlib import reload

import pytest


def test_missing_requests(requests_off):
    with pytest.raises(SystemExit) as exit_exp:
        import proxmoxer.backends.https as test_https

        # force re-importing of the module with `requests` gone so the validation is triggered
        reload(test_https)

    assert exit_exp.value.code == 1


@pytest.fixture()
def requests_off(monkeypatch):
    return monkeypatch.setitem(sys.modules, "requests", None)
