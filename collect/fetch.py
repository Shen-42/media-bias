"""Fetch discovered crash-candidate URLs and extract text with trafilatura (PLAN.md §6 step 3)."""

import argparse
import hashlib
import json
from datetime import UTC, datetime

import trafilatura

from collect.discover import fetch_tier
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


def fetch_order(urls: list[str], topic: str) -> tuple[list[str], list[str]]:
    """Crash URLs: tier 1 first, tier 2 after, others are noise (D-32, D-38).
    Other topics keep discovery order: the crash tiers do not apply to them."""
    if topic != "crash":
        return list(urls), []
    noise = [u for u in urls if fetch_tier(u) is None]
    keep = sorted((u for u in urls if fetch_tier(u)), key=fetch_tier)
    return keep, noise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("outlet")
    ap.add_argument("--db", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--topic", default="crash")
    ap.add_argument(
        "--retry-failed", action="store_true", help="requeue failures other than blocks/404s"
    )
    args = ap.parse_args()
    cfg = config.load()
    o = cfg["outlets"][args.outlet]
    f = Fetcher(delays={o["domain"]: o["crawl_delay_s"]})
    con = db.connect(args.db)
    if args.retry_failed:
        n_re = con.execute(
            "UPDATE discovered_urls SET status='new' WHERE outlet=? AND status LIKE 'failed:%'"
            " AND status NOT LIKE 'failed:blocked%' AND status != 'failed:http_404'",
            (args.outlet,),
        ).rowcount
        con.commit()
        print(f"{args.outlet}: requeued {n_re} failed urls", flush=True)
    rows = con.execute(
        "SELECT url FROM discovered_urls WHERE outlet=? AND topic_hint=? AND status='new'"
        " ORDER BY coalesce(url_date, lastmod)",
        (args.outlet, args.topic),
    ).fetchall()
    keep, noise = fetch_order([r[0] for r in rows], args.topic)
    con.executemany(
        "UPDATE discovered_urls SET status='skipped:slug_noise' WHERE url=?", [(u,) for u in noise]
    )
    con.commit()
    rows = [(u,) for u in keep][: args.limit]
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
        if n % 50 == 0 or status.startswith("failed"):
            print(f"{args.outlet} {n}/{len(rows)} {status} {url}", flush=True)
    print(f"{args.outlet} done: {len(rows)}", flush=True)


if __name__ == "__main__":
    main()
