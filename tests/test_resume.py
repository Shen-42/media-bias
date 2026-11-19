"""Collection survives outages and resumes (no network: sessions and fetchers are faked)."""

import requests

from collect import discover
from collect.http import Blocked, Fetcher
from common import db


class FakeSession:
    def __init__(self, script):
        self.script = list(script)  # each item: exception instance or (status, text)
        self.calls = 0

    def get(self, url, timeout=None, headers=None):
        self.calls += 1
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        r = requests.Response()
        r.status_code, r._content = item[0], item[1].encode()
        return r

    def head(self, url, timeout=None):
        return None


def _fetcher(monkeypatch, script):
    f = Fetcher()
    f.session = FakeSession(script)
    monkeypatch.setattr("collect.http.time.sleep", lambda s: None)
    monkeypatch.setattr(f, "_wait", lambda host: None)
    return f


def test_outage_is_waited_out_then_succeeds(monkeypatch):
    err = requests.ConnectionError()
    f = _fetcher(monkeypatch, [err, err, err, (200, "ok")])
    waited = []
    monkeypatch.setattr(f, "_wait_for_network", lambda host: waited.append(host))
    assert f.get("https://a.ca/x", check_robots=False).text == "ok"
    assert waited == ["a.ca"]


def test_after_outage_wait_challenge_still_blocks(monkeypatch):
    err = requests.ConnectionError()
    f = _fetcher(monkeypatch, [err, err, err, (200, "Just a moment...")])
    monkeypatch.setattr(f, "_wait_for_network", lambda host: None)
    try:
        f.get("https://a.ca/x", check_robots=False)
        raise AssertionError("expected Blocked")
    except Blocked:
        pass


def test_persistent_outage_raises(monkeypatch):
    err = requests.ConnectionError()
    f = _fetcher(monkeypatch, [err] * 4)
    monkeypatch.setattr(f, "_wait_for_network", lambda host: None)
    try:
        f.get("https://a.ca/x", check_robots=False)
        raise AssertionError("expected ConnectionError")
    except requests.ConnectionError:
        pass


class FakeFetcher:
    def __init__(self, fail, gateway_errors=()):
        self.fail = set(fail)
        self.gateway_errors = set(gateway_errors)
        self.seen = []

    def get(self, url):
        self.seen.append(url)
        if url in self.fail:
            raise requests.ConnectionError()
        r = requests.Response()
        r.status_code = 504 if url in self.gateway_errors else 200
        r._content = b"<url><loc>https://a.ca/2024/01/02/pedestrian-struck/</loc></url>"
        return r


def test_discovery_skips_failed_sitemap_and_resumes(tmp_path):
    con = db.connect(str(tmp_path / "t.sqlite"))
    maps = ["https://a.ca/s1.xml", "https://a.ca/s2.xml"]
    f = FakeFetcher(fail=["https://a.ca/s1.xml"])
    discover._walk(f, con, "x", maps, "2023-01-01", "2026-10-31")
    assert f.seen == maps  # s1 failed, s2 still walked
    f2 = FakeFetcher(fail=[])
    discover._walk(f2, con, "x", maps, "2023-01-01", "2026-10-31")
    assert f2.seen == ["https://a.ca/s1.xml"]  # only the failed one is retried


def test_discovery_treats_http_error_as_failed_not_empty(tmp_path):
    con = db.connect(str(tmp_path / "t.sqlite"))
    maps = ["https://a.ca/s1.xml"]
    discover._walk(
        FakeFetcher([], ["https://a.ca/s1.xml"]), con, "x", maps, "2023-01-01", "2026-10-31"
    )
    f2 = FakeFetcher([])
    discover._walk(f2, con, "x", maps, "2023-01-01", "2026-10-31")
    assert f2.seen == maps  # the 504 sitemap was not marked done
    assert con.execute("SELECT count(*) FROM discovered_urls").fetchone()[0] == 1


def test_mislabeled_gzip_body_is_read_raw(monkeypatch):
    import gzip
    import io

    f = _fetcher(monkeypatch, [requests.exceptions.ContentDecodingError()])
    waited = []
    monkeypatch.setattr(f, "_wait_for_network", lambda host: waited.append(host))
    for body, want in (
        (b"<html>plain</html>", "<html>plain</html>"),
        (gzip.compress(b"<html>gz</html>"), "<html>gz</html>"),
    ):
        r = requests.Response()
        r.status_code, r.raw = 200, io.BytesIO(body)
        r.raw.read = (lambda b: lambda decode_content=True: b)(body)
        monkeypatch.setattr(f.session, "get", lambda *a, _r=r, **k: _r)
        assert f._get_raw("https://a.ca/x").text == want
    assert waited == []
