"""URL discovery from outlet sitemaps (PLAN.md §6 step 1; DECISIONS.md D-23).

Each outlet has its own sitemap layout. URLs are kept when the slug suggests a crash,
bike lane, or transit story. Only crash candidates are fetched in v1 (D-30).
"""

import argparse
import re
from datetime import date, timedelta

from collect.http import Blocked, Fetcher
from common import config, db

CRASH_SLUG = re.compile(
    r"pedestrian|cyclist|bicycl|bike|scooter|struck|hit-by|hit-and-run|-hit-|collision|crash"
    r"|run-over|pinned|mowed|knocked-down|dragged"
)
# Fetch tiers (D-32, D-38). Tier 1 names a VRU or a strike construction; tier 2 only
# "crash"/"collision"; anything else matched by CRASH_SLUG (e.g. "prices-hit-record") is skipped.
VRU_SLUG = re.compile(
    r"pedestrian|cyclist|bicycl|bike|scooter|hit-by|hit-and-run|struck-by|run-over|pinned"
    r"|mowed|knocked-down|dragged|streetcar|ttc-bus|(?:man|woman|boy|girl|senior|child)-(?:\d+-)?"
    r"(?:struck|hit)"
)
TIER2_SLUG = re.compile(r"collision|crash")


def fetch_tier(url: str) -> int | None:
    slug = url.lower().rstrip("/").rsplit("/", 1)[-1]
    if VRU_SLUG.search(slug):
        return 1
    if TIER2_SLUG.search(slug):
        return 2
    return None


BIKE_LANE_SLUG = re.compile(r"bike-lane|bill-212|cycle-track|cycling-infrastructure")
TRANSIT_SLUG = re.compile(r"\bttc\b|-ttc-|transit|subway|-lrt|crosstown|metrolinx")
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>(?:\s*<lastmod>\s*([^<\s]+)\s*</lastmod>)?")
URL_DATE_RE = re.compile(r"/(20\d\d)/(\d\d)/(\d\d)/")


def topic_hint(url: str) -> str | None:
    slug = url.lower().rstrip("/").rsplit("/", 1)[-1]
    if BIKE_LANE_SLUG.search(slug):
        return "bike_lane"
    if CRASH_SLUG.search(slug):
        return "crash"
    if TRANSIT_SLUG.search(slug):
        return "transit"
    return None


def url_date(url: str) -> str | None:
    m = URL_DATE_RE.search(url)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def parse_sitemap(xml: str) -> list[tuple[str, str | None]]:
    return [(m.group(1).replace("&amp;", "&"), m.group(2)) for m in LOC_RE.finditer(xml)]


def _store(con, outlet: str, entries, source: str, start: str, end: str) -> int:
    n = 0
    for url, lastmod in entries:
        hint = topic_hint(url)
        if not hint:
            continue
        ud = url_date(url)
        if ud and not (start <= ud <= end):
            continue
        if not ud and lastmod and lastmod[:10] < start:
            continue
        con.execute(
            "INSERT OR IGNORE INTO discovered_urls (url, outlet, lastmod, url_date, source,"
            " topic_hint) VALUES (?,?,?,?,?,?)",
            (url, outlet, lastmod, ud, source, hint),
        )
        n += 1
    con.commit()
    return n


def citynews(f: Fetcher, con, start: str, end: str) -> None:
    index = f.get("https://toronto.citynews.ca/sitemap.xml").text
    maps = [u for u, _ in parse_sitemap(index) if "sitemap-pt-post-p" in u]
    for sm in maps:
        entries = parse_sitemap(f.get(sm).text)
        n = _store(con, "citynews", entries, sm, start, end)
        print(f"citynews {sm.rsplit('/', 1)[-1]}: {len(entries)} urls, {n} kept", flush=True)


def ctv(f: Fetcher, con, start: str, end: str) -> None:
    d, last = date.fromisoformat(start), date.fromisoformat(end)
    while d <= last:
        u = f"https://www.ctvnews.ca/arc/outboundfeeds/sitemap/{d.isoformat()}/?outputType=xml"
        entries = [(x, d.isoformat()) for x, _ in parse_sitemap(f.get(u).text) if "/toronto/" in x]
        n = _store(con, "ctv", entries, u, start, end)
        if d.day == 1:
            print(f"ctv {d}: {len(entries)} toronto urls, {n} kept", flush=True)
        d += timedelta(days=1)


def global_news(f: Fetcher, con, start: str, end: str) -> None:
    index = f.get("https://globalnews.ca/sitemap-index-2.xml").text
    maps = [u for u, _ in parse_sitemap(index) if re.search(r"/sitemap-\d+\.xml$", u)]
    for sm in maps:
        entries = parse_sitemap(f.get(sm).text)
        entries = [(u, lm) for u, lm in entries if "/news/" in u]
        n = _store(con, "global", entries, sm, start, end)
        print(f"global {sm.rsplit('/', 1)[-1]}: {len(entries)} urls, {n} kept", flush=True)


def cbc(f: Fetcher, con, start: str, end: str) -> None:
    index = f.get("https://www.cbc.ca/sitemap.xml").text
    print("cbc index:", parse_sitemap(index)[:5], flush=True)


OUTLETS = {"citynews": citynews, "ctv": ctv, "global": global_news, "cbc": cbc}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("outlet", choices=OUTLETS)
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    cfg = config.load()
    o = cfg["outlets"][args.outlet]
    f = Fetcher(delays={o["domain"]: o["crawl_delay_s"]})
    con = db.connect(args.db)
    try:
        OUTLETS[args.outlet](f, con, cfg["corpus"]["start"], cfg["corpus"]["end"])
    except Blocked as e:
        print(f"BLOCKED {args.outlet}: {e}", flush=True)
    except Exception as e:  # network failure: report, keep what was stored
        print(f"FAILED {args.outlet}: {type(e).__name__}: {e}", flush=True)
    counts = con.execute(
        "SELECT topic_hint, count(*) FROM discovered_urls WHERE outlet=? GROUP BY 1", (args.outlet,)
    ).fetchall()
    print(args.outlet, [tuple(r) for r in counts], flush=True)


if __name__ == "__main__":
    main()
