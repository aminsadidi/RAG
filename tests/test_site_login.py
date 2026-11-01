"""The scripts log in to the site with the login form (POST /login), never with the password in a URL."""

import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))
import site_login  # noqa: E402

SEEN = []


class Site(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        SEEN.append(("GET", self.path, ""))
        self.send_response(401 if "session=ok" not in (self.headers.get("cookie") or "") else 200)
        self.end_headers()
        self.wfile.write(b"page")

    def do_POST(self):
        body = self.rfile.read(int(self.headers["content-length"])).decode()
        SEEN.append(("POST", self.path, body))
        form = urllib.parse.parse_qs(body)
        if self.path == "/login" and form.get("username") == ["ci-bot"] and form.get("password") == ["s3cret&x"]:
            self.send_response(303)
            self.send_header("location", "/")
            self.send_header("set-cookie", "session=ok; Path=/; HttpOnly")
        else:
            self.send_response(401)
        self.end_headers()


@pytest.fixture
def base():
    srv = HTTPServer(("127.0.0.1", 0), Site)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    SEEN.clear()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def test_login_posts_the_form_and_keeps_the_cookie(base):
    op = site_login.login(base, user="ci-bot", password="s3cret&x")
    assert op.open(f"{base}/").status == 200
    assert SEEN[0][0] == "POST" and SEEN[0][1] == "/login"
    assert all("s3cret" not in path for _, path, _ in SEEN)  # the password never in a URL


def test_wrong_password_stops(base):
    with pytest.raises(SystemExit, match="site login failed"):
        site_login.login(base, user="ci-bot", password="wrong")
