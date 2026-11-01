"""Log in to the site with a user account (POST /login), for the scripts that use the live site.

SITE_USER and SITE_PASS: a dedicated account (the CI workflows get the CI account from the site, see
web/src/oidc.js); the owner can use SITE_USER=owner and the site's password locally. The password never goes in
a URL. Returns a urllib opener that keeps the session cookie.
"""
import http.cookiejar
import os
import urllib.error
import urllib.parse
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def login(base: str, jar: http.cookiejar.CookieJar | None = None, user: str | None = None, password: str | None = None):
    jar = jar if jar is not None else http.cookiejar.CookieJar()
    user = user if user is not None else os.environ.get("SITE_USER", "")
    password = password if password is not None else os.environ["SITE_PASS"]
    form = urllib.parse.urlencode({"username": user, "password": password}).encode()
    once = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), _NoRedirect)
    once.addheaders = [("User-Agent", "matrag-quality/1")]
    try:
        r = once.open(urllib.request.Request(f"{base}/login", form, {"content-type": "application/x-www-form-urlencoded"}), timeout=60)
        status = r.status
    except urllib.error.HTTPError as e:  # the 303 to / (not followed) comes here too
        status = e.code
    if status != 303 or not any(c.name == "session" for c in jar):
        raise SystemExit(f"site login failed ({status})")
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", "matrag-quality/1")]
    return op
