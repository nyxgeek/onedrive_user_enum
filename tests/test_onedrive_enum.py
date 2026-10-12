"""Offline regression tests for onedrive_enum.py.

All network access is mocked and the SQLite database is redirected to a temp
file, so these never touch Microsoft endpoints or the tracked data/ db.
"""
import sqlite3
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

import onedrive_enum as oe


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "create table onedrive_enum(email_address text UNIQUE, username text, domain text, "
        "tenant text, scrape_date_unix int, environment text);"
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(oe, "sqldb_location", str(path))
    return path


@pytest.fixture
def make_checker(monkeypatch):
    def _make(output=None, append="", domain="Example.com", tenant="Contoso "):
        monkeypatch.setattr(oe.UrlChecker, "test_connect", lambda self: True)
        return oe.UrlChecker(tenant, domain, "commercial", "sharepoint.com",
                             None, append, False, None, output)
    return _make


def fake_session(status_code=None, exc=None):
    session = mock.Mock()
    if exc:
        session.head.side_effect = exc
    else:
        session.head.return_value = SimpleNamespace(status_code=status_code)
    return session


def test_init_normalizes_tenant_and_domain(make_checker):
    c = make_checker()
    assert c.tenant_name == "contoso"
    assert c.domain == "example.com"
    assert c.safe_domain == "example_com"
    assert c.output is False


def test_init_output_path(make_checker, tmp_path):
    assert make_checker(output="out.txt").output_filename.endswith("out.txt")
    absolute = str(tmp_path / "abs.txt")
    assert make_checker(output=absolute).output_filename == absolute


def test_retry_session_mounts_adapters(make_checker):
    session = make_checker().requests_retry_session(retries=2)
    adapter = session.get_adapter("https://x.sharepoint.com")
    assert adapter.max_retries.total == 2
    assert 502 in adapter.max_retries.status_forcelist


@pytest.mark.parametrize("status", ["404", "301", "302"])
def test_check_url_invalid_user(make_checker, db_path, status):
    c = make_checker()
    with mock.patch.object(c, "requests_retry_session", return_value=fake_session(int(status))):
        c.check_url("jsmith")
    assert (c.validcount, c.errorcount, c.currentcount) == (0, 0, 1)


@pytest.mark.parametrize("status", [401, 403])
def test_check_url_valid_user_logged_and_written(make_checker, db_path, tmp_path, status):
    out = tmp_path / "found.txt"
    c = make_checker(output=str(out))
    session = fake_session(status)
    with mock.patch.object(c, "requests_retry_session", return_value=session):
        c.check_url("john.smith\n")
    assert c.validcount == 1
    assert out.read_text() == "john.smith@example.com\n"
    # dots become underscores in the personal-site path
    session.head.assert_called_once_with(
        "https://contoso-my.sharepoint.com/personal/john_smith_example_com/_layouts/15/onedrive.aspx",
        timeout=8.0,
    )
    rows = sqlite3.connect(db_path).execute(
        "select email_address, username, domain, tenant, environment from onedrive_enum").fetchall()
    assert rows == [("john.smith@example.com", "john.smith", "example.com", "contoso", "commercial")]


def test_check_url_append_string(make_checker, db_path):
    c = make_checker(append="1")
    session = fake_session(404)
    with mock.patch.object(c, "requests_retry_session", return_value=session):
        c.check_url("jsmith")
    assert "/personal/jsmith1_example_com/" in session.head.call_args[0][0]


def test_check_url_email_input_overrides_domain(make_checker, db_path):
    c = make_checker()
    session = fake_session(404)
    with mock.patch.object(c, "requests_retry_session", return_value=session):
        c.check_url("jsmith@other.org")
    assert "/personal/jsmith_other_org/" in session.head.call_args[0][0]


def test_check_url_unknown_status_counts_error(make_checker, db_path):
    c = make_checker()
    with mock.patch.object(c, "requests_retry_session", return_value=fake_session(500)):
        c.check_url("jsmith")
    assert (c.validcount, c.errorcount) == (0, 1)


@pytest.mark.parametrize("exc", [
    requests.Timeout("t"),
    requests.RequestException("r"),
    RuntimeError("boom"),
])
def test_check_url_exceptions_counted_not_raised(make_checker, db_path, exc):
    c = make_checker()
    with mock.patch.object(c, "requests_retry_session", return_value=fake_session(exc=exc)):
        c.check_url("jsmith")
    assert c.errorcount == 1


def test_check_url_connection_error_sleeps_and_counts(make_checker, db_path):
    c = make_checker()
    with mock.patch.object(c, "requests_retry_session",
                           return_value=fake_session(exc=requests.ConnectionError("c"))), \
         mock.patch.object(oe.time, "sleep") as sleep:
        c.check_url("jsmith")
    sleep.assert_called_once_with(3)
    assert c.errorcount == 1


def test_run_sqlite_query_roundtrip(make_checker, db_path):
    c = make_checker()
    c.run_sqlite_query("INSERT INTO onedrive_enum VALUES ('a@b.c','a','b.c','t',1,'commercial');")
    assert c.run_sqlite_query("select username from onedrive_enum;") == [("a",)]


def test_sql_insert_user_is_idempotent(make_checker, db_path):
    c = make_checker()
    for _ in range(2):
        c.sql_insert_user("a@b.c", "a", "b.c", "t", "1", "commercial")
    assert c.run_sqlite_query("select count(*) from onedrive_enum;") == [(1,)]


def _autodiscover(*domains):
    body = "".join(f"<Domain>{d}</Domain>" for d in domains)
    return SimpleNamespace(content=body.encode())


def test_lookup_tenant_single_match(capsys):
    resp = _autodiscover("example.com", "contoso.onmicrosoft.com", "contoso.mail.onmicrosoft.com")
    with mock.patch.object(oe.requests, "post", return_value=resp), \
         mock.patch.object(oe.socket, "gethostbyname", return_value="1.2.3.4"):
        assert oe.lookup_tenant("example.com") == "contoso"


def test_lookup_tenant_prefers_mail_record_match():
    resp = _autodiscover("a.onmicrosoft.com", "b.onmicrosoft.com", "b.mail.onmicrosoft.com")
    with mock.patch.object(oe.requests, "post", return_value=resp), \
         mock.patch.object(oe.socket, "gethostbyname", return_value="1.2.3.4"):
        assert oe.lookup_tenant("example.com") == "b"


def test_lookup_tenant_no_tenants_exits():
    with mock.patch.object(oe.requests, "post", return_value=_autodiscover("example.com")), \
         pytest.raises(SystemExit):
        oe.lookup_tenant("example.com")


def test_lookup_tenant_no_onedrive_host_exits():
    resp = _autodiscover("contoso.onmicrosoft.com")
    with mock.patch.object(oe.requests, "post", return_value=resp), \
         mock.patch.object(oe.socket, "gethostbyname", side_effect=oe.socket.gaierror), \
         pytest.raises(SystemExit):
        oe.lookup_tenant("example.com")


def test_lookup_tenant_network_error_returns_none():
    with mock.patch.object(oe.requests, "post", side_effect=requests.ConnectionError("x")):
        assert oe.lookup_tenant("example.com") is None
