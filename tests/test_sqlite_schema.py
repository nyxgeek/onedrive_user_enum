import sqlite3

import onedrive_enum as ode


def _tables(path):
    conn = sqlite3.connect(path)
    try:
        # sqlite_sequence is created implicitly by AUTOINCREMENT, so skip internal tables.
        rows = conn.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'").fetchall()
    finally:
        conn.close()
    return {name for (name,) in rows}


def test_sql_create_table_creates_missing_dir_and_both_tables(monkeypatch, tmp_path, checker):
    db_path = tmp_path / "missing" / "dir" / "x.db"
    monkeypatch.setattr(ode, "sqldb_location", str(db_path))

    checker.sql_create_table()

    assert db_path.exists()
    assert _tables(str(db_path)) == {"onedrive_enum", "onedrive_log"}


def test_sql_create_table_is_idempotent(monkeypatch, tmp_path, checker):
    db_path = tmp_path / "x.db"
    monkeypatch.setattr(ode, "sqldb_location", str(db_path))

    checker.sql_create_table()
    checker.sql_create_table()

    assert _tables(str(db_path)) == {"onedrive_enum", "onedrive_log"}


def test_insert_user_round_trip(monkeypatch, checker):
    monkeypatch.setattr(ode, "enable_db", True)
    checker.sql_create_table()

    checker.sql_insert_user("jsmith@contoso.com", "jsmith", "contoso.com", "contoso", "1", "commercial")
    rows = checker.run_sqlite_query("select email_address, username, domain, tenant from onedrive_enum")

    assert rows == [("jsmith@contoso.com", "jsmith", "contoso.com", "contoso")]


def test_run_sqlite_query_returns_none_when_db_cannot_open(monkeypatch, tmp_path, checker):
    # A directory cannot be opened as a sqlite database.
    monkeypatch.setattr(ode, "sqldb_location", str(tmp_path))

    assert checker.run_sqlite_query("select 1") is None


def test_init_creates_schema_before_test_connect(monkeypatch, tmp_path):
    db_path = tmp_path / "x.db"
    monkeypatch.setattr(ode, "sqldb_location", str(db_path))
    monkeypatch.setattr(ode, "enable_db", True)
    seen = {}

    def fake_test_connect(self):
        # Schema must already exist when the first connectivity check runs.
        seen["tables"] = _tables(str(db_path))
        return True

    monkeypatch.setattr(ode.UrlChecker, "test_connect", fake_test_connect)

    ode.UrlChecker("contoso", "contoso.com", "commercial", "sharepoint.com", None, "", False, None, False)

    assert seen["tables"] == {"onedrive_enum", "onedrive_log"}


def test_init_skips_schema_when_db_disabled(monkeypatch, tmp_path):
    db_path = tmp_path / "x.db"
    monkeypatch.setattr(ode, "sqldb_location", str(db_path))
    monkeypatch.setattr(ode, "enable_db", False)
    monkeypatch.setattr(ode.UrlChecker, "test_connect", lambda self: True)

    ode.UrlChecker("contoso", "contoso.com", "commercial", "sharepoint.com", None, "", False, None, False)

    assert not db_path.exists()
