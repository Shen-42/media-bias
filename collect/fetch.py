"""Fetch discovered crash-candidate URLs and extract text with trafilatura (PLAN.md §6 step 3)."""

import argparse
import hashlib
import json
from datetime import UTC, datetime

import trafilatura

from collect.discover import VRU_SLUG
from collect.http import Blocked, Fetcher, save_raw
from common import config, db


def article_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16]


def extract(html: str, url: str) -> dict | None:
    out = trafilatura.extract(
        html, url=url, output_format="json", with_metadata=True, include_comments=False
    )
    if not out:
        return None
    d = json.loads(out)
    return {"title": d.get("title"), "published": (d.get("date") or "")[:10], "text": d.get("text")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("outlet")
    ap.add_argument("--db", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--topic", default="crash")
    args = ap.parse_args()
    cfg = config.load()
    o = cfg["outlets"][args.outlet]
    f = Fetcher(delays={o["domain"]: o["crawl_delay_s"]})
    con = db.connect(args.db)
    rows = con.execute(
        "SELECT url FROM discovered_urls WHERE outlet=? AND topic_hint=? AND status='new'"
        " ORDER BY coalesce(url_date, lastmod)",
        (args.outlet, args.topic),
    ).fetchall()
    # Tier 1 first: slugs naming a VRU or a strike verb; "crash/collision only" slugs after (D-32).
    rows = sorted(rows, key=lambda r: 0 if VRU_SLUG.search(r[0].lower()) else 1)[: args.limit]
    start, end = cfg["corpus"]["start"], cfg["corpus"]["end"]
    for n, (url,) in enumerate(rows):
        status = "fetched"
        try:
            r = f.get(url)
            rec = extract(r.text, url) if r.ok else None
            if rec is None:
                status = f"failed:http_{r.status_code}" if not r.ok else "failed:extract"
            elif rec["published"] and not (start <= rec["published"] <= end):
                status = "skipped:out_of_window"
            else:
                con.execute(
                    "INSERT OR IGNORE INTO articles (id, outlet, url, title, published, fetched_at,"
                    " raw_path, text) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        article_id(url),
                        args.outlet,
                        url,
                        rec["title"],
                        rec["published"],
                        datetime.now(UTC).isoformat(timespec="seconds"),
                        save_raw(url, r.text),
                        rec["text"],
                    ),
                )
        except Blocked as e:
            status = f"failed:blocked:{e}"[:200]
        except Exception as e:  # network error: record, continue
            status = f"failed:{type(e).__name__}"
        con.execute("UPDATE discovered_urls SET status=? WHERE url=?", (status, url))
        con.commit()
        if n % 50 == 0:
            print(f"{args.outlet} {n}/{len(rows)} {status} {url}", flush=True)
    print(f"{args.outlet} done: {len(rows)}", flush=True)


if __name__ == "__main__":
    main()
