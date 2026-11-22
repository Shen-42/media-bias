"""Copy Global News regional articles from the main corpus into the cities database (D-100).

Global's sitemaps are national, so the main crawl already fetched its BC and Montreal crash
stories; they were dropped from the Toronto corpus by the Toronto filter. The section in the
title ("... - BC | Globalnews.ca") assigns the comparison outlet.

    python -m collect.compare --main data/corpus.sqlite --cities data/cities.sqlite
"""

import argparse

from common import db

SECTIONS = {"BC": "global_van", "Montreal": "global_mtl"}


def outlet_for(title: str | None) -> str | None:
    for section, outlet in SECTIONS.items():
        if title and f" - {section} | Global" in title:
            return outlet
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", default=None)
    ap.add_argument("--cities", required=True)
    args = ap.parse_args()
    src, dst = db.connect(args.main), db.connect(args.cities)
    n = 0
    for a in src.execute(
        "SELECT id, url, title, published, fetched_at, raw_path, text FROM articles"
        " WHERE outlet = 'global'"
    ):
        outlet = outlet_for(a["title"])
        if outlet:
            dst.execute(
                "INSERT OR IGNORE INTO articles (id, outlet, url, title, published, fetched_at,"
                " raw_path, text) VALUES (?,?,?,?,?,?,?,?)",
                (a["id"], outlet, a["url"], a["title"], a["published"], a["fetched_at"],
                 a["raw_path"], a["text"]),
            )  # fmt: skip
            n += 1
    dst.commit()
    print(f"copied {n} Global regional articles", flush=True)


if __name__ == "__main__":
    main()
