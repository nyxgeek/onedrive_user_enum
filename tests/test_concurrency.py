import concurrent.futures
import itertools
import os
import threading
import time

import pytest
import requests

import onedrive_enum as ode

THREADS = 8
LINES = 1000


class Stats:
    """Thread-safe counters shared by the fake sessions."""

    def __init__(self):
        self.lock = threading.Lock()
        self.in_flight = 0
        self.peak = 0
        self.sessions = 0
        self.segments = []
        self.pool = None
        self.queue_peak = 0


class ScriptedResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class ConcurrentSession:
    # Every 4th name is 403 (valid), 404 (invalid), 500 (unknown), or a timeout (error).
    def __init__(self, stats):
        self.stats = stats

    def head(self, url, timeout=None):
        segment = url.split("/personal/")[1].split("/")[0]
        index = int(segment[4:8])
        with self.stats.lock:
            self.stats.in_flight += 1
            self.stats.peak = max(self.stats.peak, self.stats.in_flight)
            self.stats.segments.append(segment)
            if self.stats.pool is not None:
                queued = self.stats.pool._work_queue.qsize()
                self.stats.queue_peak = max(self.stats.queue_peak, queued)
        try:
            time.sleep(0.001)
        finally:
            with self.stats.lock:
                self.stats.in_flight -= 1
        if index % 4 == 3:
            raise requests.Timeout("scripted timeout")
        return ScriptedResponse({0: 403, 1: 404, 2: 500}[index % 4])


def counting_factory(stats):
    def factory(*args, **kwargs):
        with stats.lock:
            stats.sessions += 1
        return ConcurrentSession(stats)
    return factory


@pytest.fixture
def stats(checker):
    s = Stats()
    checker.requests_retry_session = counting_factory(s)
    return s


def prepare_run(checker, tmp_path, monkeypatch, lines=LINES):
    monkeypatch.setattr(ode, "thread_count", THREADS, raising=False)
    monkeypatch.setattr(ode, "exitRequested", False)
    path = tmp_path / "users.txt"
    path.write_text("".join(f"user{i:04d}\n" for i in range(lines)))
    checker.userdata = str(path)
    checker.skip_tried = False
    checker.status = "0"
    checker.start_unix_time = 0
    completed = []
    checker.sql_log_completed_run = lambda userlist: completed.append(userlist)
    checker.completed = completed
    return checker


@pytest.fixture
def run_checker(checker, stats, tmp_path, monkeypatch):
    return prepare_run(checker, tmp_path, monkeypatch)


@pytest.fixture
def recording_pool(stats, monkeypatch):
    # Record the executor so the fake session can sample its work queue.
    class RecordingPool(concurrent.futures.ThreadPoolExecutor):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            stats.pool = self

    monkeypatch.setattr(concurrent.futures, "ThreadPoolExecutor", RecordingPool)


def test_check_user_file_exact_counts_and_bounded_concurrency(run_checker, stats, capsys):
    run_checker.check_user_file()

    expected = [f"user{i:04d}_contoso_com" for i in range(LINES)]
    assert sorted(stats.segments) == sorted(expected)
    assert run_checker.currentcount == LINES
    assert run_checker.totalcount == LINES
    assert run_checker.validcount == LINES // 4
    assert run_checker.errorcount == LINES // 2
    assert 1 < stats.peak <= THREADS
    assert stats.sessions <= THREADS
    assert run_checker.completed == [run_checker.userdata]


def test_status_bar_is_throttled_and_final_totals_printed(run_checker, capsys):
    run_checker.check_user_file()

    out = capsys.readouterr().out
    assert out.count(" tested, ") < 100
    assert f"{LINES} / {LINES} tested" in out


def test_session_reused_across_requests_on_one_thread(checker, stats):
    for i in range(20):
        checker.check_url(f"user{i:04d}")

    assert stats.sessions == 1
    assert len(stats.segments) == 20


def test_graceful_cancel_stops_before_submitting_work(run_checker, stats, monkeypatch):
    monkeypatch.setattr(ode, "exitRequested", True)

    with pytest.raises(SystemExit) as excinfo:
        run_checker.check_user_file()

    assert excinfo.value.code == 0
    assert run_checker.status == "1337000004"
    assert stats.segments == []


def test_in_flight_work_stays_bounded(checker, stats, recording_pool, tmp_path, monkeypatch):
    prepare_run(checker, tmp_path, monkeypatch, lines=2000)

    checker.check_user_file()

    assert stats.queue_peak <= 2 * THREADS


def test_output_file_gets_each_valid_user_once(run_checker, stats, tmp_path):
    run_checker.output = True
    run_checker.output_filename = str(tmp_path / "found.txt")

    run_checker.check_user_file()

    with open(run_checker.output_filename) as f:
        found = [line.rstrip("\n") for line in f]
    expected = [f"user{i:04d}@contoso.com" for i in range(0, LINES, 4)]
    assert sorted(found) == sorted(expected)
    assert len(found) == LINES // 4


def test_exception_escaping_check_url_is_reported_and_counted(run_checker, stats, monkeypatch, capsys):
    # Fail the PAUSEFILE probe, which runs before check_url's try block, on every fifth call.
    real_isfile = os.path.isfile
    calls = itertools.count()

    def flaky_isfile(path):
        if path == "/tmp/PAUSEFILE" and next(calls) % 5 == 0:
            raise OSError("pause probe failed")
        return real_isfile(path)

    monkeypatch.setattr(os.path, "isfile", flaky_isfile)

    run_checker.check_user_file()

    err = capsys.readouterr().err
    assert err.count("Traceback (most recent call last)") == LINES // 5
    assert "OSError: pause probe failed" in err
    assert run_checker.currentcount == LINES == run_checker.totalcount
    assert run_checker.errorcount >= LINES // 5
