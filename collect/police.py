"""Toronto Police news releases from Wayback Machine copies only (PLAN.md §6 step 2).

The TPS site blocks scripted access, so releases are read from the Internet Archive.
Release IDs are sequential; only archived IDs can be collected (about 42% of the window).
"""

import argparse
import html as htmllib
import json
import re
import urllib.parse
from datetime import datetime

from collect.http import Blocked, Fetcher
from common import config, db

CDX = "https://web.archive.org/cdx/search/cdx"
ID_RE = re.compile(r"/news-releases/(\d+)/?$")
PUBLISHED_RE = re.compile(
    r"Published:\s*(?:\w+day,\s*)?([A-Z][a-z]+ \d{1,2}, \d{4})(?:,\s*(\d{1,2}:\d{2}\s*[AP]M))?"
)
COLLISION_RE = re.compile(
    r"collision|struck|pedestrian|cyclist|hit and run|hit-and-run|fail to remain", re.I
)


def enumerate_ids(fetcher: Fetcher, prefix: str) -> dict[int, tuple[str, str]]:
    """Return {release_id: (timestamp, original_url)} for archived 200 captures."""
    out: dict[int, tuple[str, str]] = {}
    key = None
    while True:
        params = {
            "url": prefix,
            "matchType": "prefix",
            "from": "2022",
            "output": "json",
            "fl": "timestamp,original,statuscode",
            "collapse": "urlkey",
            "limit": "5000",
            "showResumeKey": "true",
            "filter": ["original:.*/news-releases/[0-9]+/?$", "statuscode:200"],
        }
        if key:
            params["resumeKey"] = key
        r = fetcher.get(CDX + "?" + urllib.parse.urlencode(params, doseq=True), check_robots=False)
        rows = json.loads(r.text)[1:]
        key = rows[-1][0] if len(rows) >= 2 and len(rows[-1]) == 1 else None
        for row in rows:
            if len(row) == 3 and (m := ID_RE.search(row[1])):
                out.setdefault(int(m.group(1)), (row[0], row[1]))
        if not key:
            return out


def parse_release(html: str) -> dict:
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    title = re.sub(r"\s+", " ", htmllib.unescape(title.group(1))).strip() if title else None
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    text = htmllib.unescape(re.sub(r"<[^>]+>", "\n", text))
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    body = "\n".join(lines)
    published = None
    if m := PUBLISHED_RE.search(body):
        try:
            published = datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat()
        except ValueError:
            published = None
    # Release body: from the "Published:" line to the end-of-release boilerplate.
    start = body.find("Published:")
    end_marks = [body.find(s) for s in ("For more news, visit", "Corporate Communications")]
    end = min([e for e in end_marks if e > start] or [len(body)])
    release = body[start:end] if start >= 0 else body
    release = re.sub(r"^Published:[^\n]*\n(Share \(opens in new window\)\n)?", "", release)
    return {"title": title, "published": published, "text": release.strip()}


def is_collision(title: str | None, text: str) -> bool:
    return bool(COLLISION_RE.search((title or "") + " " + text[:600]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    cfg = config.load()
    con = db.connect(args.db)
    fetcher = Fetcher(delays={"web.archive.org": cfg["police"]["wayback_delay_s"]})
    ids = enumerate_ids(fetcher, cfg["police"]["wayback_prefix"])
    print(f"archived release ids: {len(ids)}", flush=True)
    done = {r[0] for r in con.execute("SELECT id FROM police_releases WHERE fetch_status='ok'")}
    start, end = cfg["corpus"]["start"], cfg["corpus"]["end"]
    # IDs below 54700 predate 2023 (54000 = Sept 2022, 54807 = first in Jan 2023).
    todo = sorted(i for i in ids if i >= 54700 and i not in done)[: args.limit]
    for n, rid in enumerate(todo):
        ts, url = ids[rid]
        try:
            r = fetcher.get(f"https://web.archive.org/web/{ts}id_/{url}", check_robots=False)
            rec = parse_release(r.text) if r.ok else {"title": None, "published": None, "text": ""}
            status = "ok" if r.ok else f"http_{r.status_code}"
        except (Blocked, Exception) as e:  # noqa: B014 - record and continue
            rec, status = (
                {"title": None, "published": None, "text": ""},
                f"error:{type(e).__name__}",
            )
        in_window = rec["published"] is not None and start <= rec["published"] <= end
        con.execute(
            "INSERT OR REPLACE INTO police_releases VALUES (?,?,?,?,?,?,?,?)",
            (
                rid,
                url,
                ts,
                rec["title"],
                rec["published"],
                rec["text"] if in_window else "",
                int(in_window and is_collision(rec["title"], rec["text"])),
                status,
            ),
        )
        con.commit()
        if n % 100 == 0:
            print(f"{n}/{len(todo)} id={rid} {rec['published']} {status}", flush=True)


if __name__ == "__main__":
    main()
