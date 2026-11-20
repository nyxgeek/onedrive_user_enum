import threading

import pytest

import onedrive_enum as ode

ode.verbose = False
ode.debug = False
ode.enable_db = False


class FakeResponse:
    status_code = 404


class UrlRecorder:
    """Collects every URL requested through the fake session, safe across threads."""

    def __init__(self):
        self._lock = threading.Lock()
        self.urls = []

    def record(self, url):
        with self._lock:
            self.urls.append(url)


class FakeSession:
    def __init__(self, recorder):
        self.recorder = recorder

    def head(self, url, timeout=None):
        self.recorder.record(url)
        return FakeResponse()


@pytest.fixture(autouse=True)
def isolated_sqlite_db(monkeypatch, tmp_path):
    # Never let a test touch the committed data/onedrive_enum.db.
    monkeypatch.setattr(ode, "sqldb_location", str(tmp_path / "onedrive_enum.db"))


@pytest.fixture
def url_recorder():
    return UrlRecorder()


@pytest.fixture
def checker(url_recorder):
    # Bypass __init__, which makes a live test_connect() call.
    c = object.__new__(ode.UrlChecker)
    c.tenant_name = "contoso"
    c.domain = "contoso.com"
    c.safe_domain = "contoso_com"
    c.endpoint = "sharepoint.com"
    c.appendString = ""
    c.environment = "commercial"
    c.mysql_enabled = False
    c.output = False
    c.errorcount = c.validcount = c.currentcount = c.totalcount = 0
    c.requests_retry_session = lambda *a, **k: FakeSession(url_recorder)
    return c
