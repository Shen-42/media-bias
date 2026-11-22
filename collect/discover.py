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


BIKE_LANE_SLUG = re.compile(
    r"bike-lane|bill-212|cycle-track|cycling-infrastructure|bikeway|bike-network|bike-route"
    r"|cycling-(?:network|plan|lanes?|route|grid|safety)|reducing-gridlock|gridlock-act"
    r"|(?:bloor|yonge|university|danforth|avenue-road|queens-park)[a-z-]*-lanes"
    r"|(?:protected|separated|cycling)-lanes?"
)  # D-61: slugs that name the lanes without "bike-lane"
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


def _store(con, outlet: str, entries, source: str, start: str, end: str, default_hint=None) -> int:
    n = 0
    for url, lastmod in entries:
        hint = topic_hint(url) or default_hint
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


def _sitemaps_done(con) -> set[str]:
    con.execute("CREATE TABLE IF NOT EXISTS sitemaps_done (url TEXT PRIMARY KEY, outlet TEXT)")
    return {r[0] for r in con.execute("SELECT url FROM sitemaps_done")}


RESCAN = False  # set by --rescan: re-read finished sitemaps, add only new URLs (D-61)


def _walk(
    f: Fetcher,
    con,
    outlet: str,
    maps: list[str],
    start: str,
    end: str,
    keep=None,
    default_hint=None,
) -> None:
    """Fetch each sitemap once. Finished ones are recorded so a rerun resumes; a failed one is
    logged and left for the rerun instead of aborting the outlet."""
    done = set() if RESCAN else _sitemaps_done(con)
    failed = 0
    for sm in maps:
        if sm in done:
            continue
        try:
            r = f.get(sm)
            if r.status_code != 200:  # e.g. 504 after retries: not an empty sitemap
                raise RuntimeError(f"http_{r.status_code}")
            entries = parse_sitemap(r.text)
        except Blocked:
            raise
        except Exception as e:  # network or parse error: log, continue, retry on rerun
            failed += 1
            print(f"{outlet} FAILED sitemap {sm}: {type(e).__name__} {e}", flush=True)
            continue
        if keep:
            entries = keep(sm, entries)
        n = _store(con, outlet, entries, sm, start, end, default_hint)
        con.execute("INSERT OR IGNORE INTO sitemaps_done VALUES (?,?)", (sm, outlet))
        con.commit()
        print(f"{outlet} {sm.rsplit('/', 1)[-1][:60]}: {len(entries)} urls, {n} kept", flush=True)
    print(f"{outlet}: {failed} sitemaps failed (rerun to retry)", flush=True)


def _citynews(f: Fetcher, con, start: str, end: str, host: str, outlet: str) -> None:
    index = f.get(f"https://{host}/sitemap.xml").text
    maps = [u for u, _ in parse_sitemap(index) if "sitemap-pt-post-p" in u]
    _walk(f, con, outlet, maps, start, end)


def citynews(f: Fetcher, con, start: str, end: str) -> None:
    _citynews(f, con, start, end, "toronto.citynews.ca", "citynews")


def citynews_van(f: Fetcher, con, start: str, end: str) -> None:
    _citynews(f, con, start, end, "vancouver.citynews.ca", "citynews_van")


def citynews_mtl(f: Fetcher, con, start: str, end: str) -> None:
    _citynews(f, con, start, end, "montreal.citynews.ca", "citynews_mtl")


def ctv(
    f: Fetcher, con, start: str, end: str, section: str = "toronto", outlet: str = "ctv"
) -> None:
    d, last = date.fromisoformat(start), date.fromisoformat(end)
    maps = []
    while d <= last:
        maps.append(
            f"https://www.ctvnews.ca/arc/outboundfeeds/sitemap/{d.isoformat()}/?outputType=xml"
        )
        d += timedelta(days=1)

    def keep(sm, entries):
        day = re.search(r"/sitemap/(\d{4}-\d{2}-\d{2})/", sm).group(1)
        return [(x, day) for x, _ in entries if re.search(f"/{section}/", x)]

    _walk(f, con, outlet, maps, start, end, keep)


def ctv_cities(f: Fetcher, con, start: str, end: str) -> None:
    """One walk of the shared daily sitemaps for both comparison cities (D-100): URLs are
    stored under ctv_cities, then split by section."""
    ctv(f, con, start, end, section="(?:vancouver|montreal)", outlet="ctv_cities")
    for city, outlet in (("vancouver", "ctv_van"), ("montreal", "ctv_mtl")):
        con.execute(
            "UPDATE discovered_urls SET outlet=? WHERE outlet='ctv_cities' AND url LIKE ?",
            (outlet, f"%/{city}/%"),
        )
    con.commit()


def global_news(f: Fetcher, con, start: str, end: str) -> None:
    index = f.get("https://globalnews.ca/sitemap-index-2.xml").text
    maps = [u for u, _ in parse_sitemap(index) if re.search(r"/sitemap-\d+\.xml$", u)]
    _walk(
        f, con, "global", maps, start, end, lambda sm, e: [(u, lm) for u, lm in e if "/news/" in u]
    )


def cbc(f: Fetcher, con, start: str, end: str) -> None:
    index = f.get("https://www.cbc.ca/sitemap.xml").text
    print("cbc index:", parse_sitemap(index)[:5], flush=True)


def _wp_posts(f: Fetcher, index_url: str) -> list[str]:
    return [u for u, _ in parse_sitemap(f.get(index_url).text) if "post-sitemap" in u]


# Urbanist outlets (D-99) use plain slugs, so every in-window post is kept ("other" when the
# slug names no topic) and topics come from the text. Cycling Magazine is mostly racing, so
# only slug-matched posts are kept there.
def spacing(f: Fetcher, con, start: str, end: str) -> None:
    maps = _wp_posts(f, "https://spacing.ca/toronto/sitemap_index.xml")
    _walk(f, con, "spacing", maps, start, end, default_hint="other")


def thelocal(f: Fetcher, con, start: str, end: str) -> None:
    maps = _wp_posts(f, "https://thelocal.to/sitemap_index.xml")
    _walk(f, con, "thelocal", maps, start, end, default_hint="other")


def cyclingmag(f: Fetcher, con, start: str, end: str) -> None:
    maps = _wp_posts(f, "https://cyclingmagazine.ca/sitemap_index.xml")
    _walk(f, con, "cyclingmag", maps, start, end)


OUTLETS = {
    "citynews": citynews,
    "ctv": ctv,
    "global": global_news,
    "cbc": cbc,
    "citynews_van": citynews_van,
    "citynews_mtl": citynews_mtl,
    "ctv_cities": ctv_cities,
    "spacing": spacing,
    "thelocal": thelocal,
    "cyclingmag": cyclingmag,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("outlet", choices=OUTLETS)
    ap.add_argument("--db", default=None)
    ap.add_argument("--rescan", action="store_true", help="re-read finished sitemaps")
    args = ap.parse_args()
    global RESCAN
    RESCAN = args.rescan
    cfg = config.load()
    o = cfg["outlets"].get(args.outlet) or cfg["outlets"]["ctv"]  # ctv_cities shares CTV
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
