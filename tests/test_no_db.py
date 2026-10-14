import onedrive_enum as ode
import pytest


class Fake401Response:
    status_code = 401


class Fake401Session:
    def head(self, url, timeout=None):
        return Fake401Response()


@pytest.fixture
def no_db(monkeypatch):
    monkeypatch.setattr(ode, "enable_db", False)


@pytest.fixture
def db_calls(monkeypatch):
    # Records every SQL query that reaches either backend.
    calls = []

    def fake_sqlite(self, query):
        calls.append(("sqlite", query))
        return []

    def fake_mysql(self, query):
        calls.append(("mysql", query))
        return []

    monkeypatch.setattr(ode.UrlChecker, "run_sqlite_query", fake_sqlite)
    monkeypatch.setattr(ode.UrlChecker, "run_mysql_query", fake_mysql)
    return calls


def test_valid_user_is_not_written_with_no_db(no_db, db_calls, checker):
    checker.requests_retry_session = lambda *a, **k: Fake401Session()

    checker.check_url("jsmith")

    assert db_calls == []


def test_insert_user_is_gated_by_no_db(no_db, db_calls, checker):
    checker.sql_insert_user("jsmith@contoso.com", "jsmith", "contoso.com", "contoso", "1", "commercial")

    assert db_calls == []


def test_check_for_previous_runs_is_gated_by_no_db(no_db, db_calls, checker):
    checker.sql_check_for_previous_runs("USERNAMES/test.txt")

    assert db_calls == []


def test_check_tried_usernames_is_gated_by_no_db(no_db, db_calls, checker):
    assert checker.sql_check_tried_usernames() == []
    assert db_calls == []


def test_insert_user_writes_when_db_enabled(monkeypatch, db_calls, checker):
    # Positive control: proves the spy sees a write when the DB is enabled.
    monkeypatch.setattr(ode, "enable_db", True)

    checker.sql_insert_user("jsmith@contoso.com", "jsmith", "contoso.com", "contoso", "1", "commercial")

    assert len(db_calls) == 1
    assert db_calls[0][0] == "sqlite"
