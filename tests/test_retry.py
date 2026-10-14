import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from requests.adapters import HTTPAdapter

import onedrive_enum as ode

PATH = "/personal/jsmith_contoso_com/_layouts/15/onedrive.aspx"


class ScriptedHandler(BaseHTTPRequestHandler):
    # Answers each HEAD with the next scripted (status, headers) pair, then 404.
    def do_HEAD(self):
        server = self.server
        with server.lock:
            server.hits += 1
            status, headers = server.script.pop(0) if server.script else (404, {})
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture
def scripted_server():
    servers = []

    def start(script):
        server = ThreadingHTTPServer(("127.0.0.1", 0), ScriptedHandler)
        server.script = list(script)
        server.hits = 0
        server.lock = threading.Lock()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return server

    yield start

    for server in servers:
        server.shutdown()
        server.server_close()


def local_url(server):
    return f"http://127.0.0.1:{server.server_address[1]}{PATH}"


def test_429_without_retry_after_is_retried(checker, scripted_server):
    # urllib3 only retries 429 when Retry-After is present, so this needs 429 in status_forcelist.
    server = scripted_server([(429, {})])

    session = ode.UrlChecker.requests_retry_session(checker, backoff_factor=0)
    r = session.head(local_url(server), timeout=8)

    assert r.status_code == 404
    assert server.hits == 2


def test_429_with_retry_after_is_retried(checker, scripted_server):
    server = scripted_server([(429, {"Retry-After": "1"})])

    session = ode.UrlChecker.requests_retry_session(checker, backoff_factor=0)
    r = session.head(local_url(server), timeout=8)

    assert r.status_code == 404
    assert server.hits == 2


def test_500_is_still_retried_until_success(checker, scripted_server):
    server = scripted_server([(500, {})])

    session = ode.UrlChecker.requests_retry_session(checker, backoff_factor=0)
    r = session.head(local_url(server), timeout=8)

    assert r.status_code == 404
    assert server.hits == 2


def test_check_url_429_then_404_is_not_an_error(checker, scripted_server, monkeypatch):
    server = scripted_server([(429, {})])

    # Route check_url's https SharePoint URL to the local server, keeping the real Retry policy.
    session = ode.UrlChecker.requests_retry_session(checker, backoff_factor=0)
    base = f"http://127.0.0.1:{server.server_address[1]}"

    class LocalAdapter(HTTPAdapter):
        def send(self, request, **kwargs):
            request.url = request.url.replace(request.url.split("/personal/")[0], base, 1)
            return super().send(request, **kwargs)

    session.mount("https://", LocalAdapter(max_retries=session.get_adapter("https://").max_retries))
    monkeypatch.setattr(checker, "requests_retry_session", lambda *a, **k: session)

    checker.check_url("jsmith")

    assert server.hits == 2
    assert checker.errorcount == 0
