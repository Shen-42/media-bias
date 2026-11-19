"""Polite HTTP fetcher: robots.txt check, per-domain delay, retries, raw cache in data/raw.

It never tries to get around bot protection. A challenge page or 403 is recorded as a failure.
"""

import gzip
import hashlib
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests

from common import config

CHALLENGE_MARKERS = ("Just a moment...", "cf-chl", "challenge-platform")


class Blocked(Exception):
    """The site refused scripted access (403, challenge page, or robots.txt)."""


class Fetcher:
    def __init__(self, delays: dict[str, float] | None = None):
        cfg = config.load()["fetch"]
        self.ua = cfg["user_agent"]
        self.min_delay = cfg["min_delay_s"]
        self.timeout = cfg["timeout_s"]
        self.delays = delays or {}
        self.session = requests.Session()
        self.session.headers["User-Agent"] = self.ua
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _wait(self, host: str) -> None:
        delay = max(self.min_delay, self.delays.get(host, 0.0))
        elapsed = time.monotonic() - self._last.get(host, 0.0)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last[host] = time.monotonic()

    def allowed(self, url: str) -> bool:
        u = urlparse(url)
        host = u.netloc
        if host not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            self._wait(host)
            try:
                r = self.session.get(f"{u.scheme}://{host}/robots.txt", timeout=self.timeout)
                if r.status_code in (401, 403):
                    rp.disallow_all = True
                elif r.status_code >= 400:
                    rp.allow_all = True
                else:
                    rp.parse(r.text.splitlines())
            except requests.RequestException:
                rp.disallow_all = True  # unreachable robots.txt: do not crawl
            self._robots[host] = rp
        return self._robots[host].can_fetch(self.ua, url)

    def get(self, url: str, retries: int = 3, check_robots: bool = True) -> requests.Response:
        if check_robots and not self.allowed(url):
            raise Blocked(f"robots.txt disallows {url}")
        host = urlparse(url).netloc
        for attempt in range(retries):
            self._wait(host)
            try:
                r = self.session.get(url, timeout=self.timeout)
            except requests.RequestException:
                if attempt == retries - 1:
                    raise
                time.sleep(10 * (attempt + 1))
                continue
            if r.status_code == 403 or any(m in r.text[:5000] for m in CHALLENGE_MARKERS):
                raise Blocked(f"{r.status_code} challenge/forbidden at {url}")
            if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(30 * (attempt + 1))
                continue
            return r
        return r


def raw_path(url: str) -> Path:
    h = hashlib.sha1(url.encode()).hexdigest()
    host = urlparse(url).netloc
    return config.path(f"{config.load()['corpus']['raw_dir']}/{host}/{h}.html.gz")


def save_raw(url: str, html: str) -> str:
    p = raw_path(url)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write(html)
    return str(p.relative_to(config.ROOT))


def load_raw(rel: str) -> str:
    with gzip.open(config.ROOT / rel, "rt", encoding="utf-8") as f:
        return f.read()
