"""v1.5 aggregate tables (bike lanes and transit).

Corpus counts, quoted source roles and the BABE loaded-language score (not validated).
Stance and frame tables come from the annotated measurement sample instead
(analysis/measure_v15.py, D-88, D-90); no model stance or frame passed validation.

Rates are sentence shares with article-cluster bootstrap 95% CIs (analysis.aggregate.rate_ci).
Every table is split by text_source (quoted, attributed, newsroom); they are never pooled
(CLAUDE.md, D-81).
Bill 212 periods come from analysis/timeline_bill212.csv.
"""

import argparse
import json

import pandas as pd

from analysis.aggregate import TABLES, rates
from common import config, db
from nlp import v15

TIMELINE = config.ROOT / "analysis" / "timeline_bill212.csv"


def periods() -> list[tuple[str, str]]:
    """(start date, period name); a sentence belongs to the last period starting on or before it."""
    t = pd.read_csv(TIMELINE)
    names = {
        "2024-10-31": "announced",
        "2024-11-25": "law_in_force",
        "2025-04-22": "injunction",
        "2025-07-30": "struck_down",
        "2026-08-14": "appeal_allowed",
    }
    out = [("0000", "before_plan")]
    out += [(d, names[d]) for d in t["date"] if d in names]
    return out


def period_of(date: str, ps: list[tuple[str, str]]) -> str:
    name = ps[0][1]
    for start, n in ps:
        if date and date[:10] >= start:
            name = n
    return name


def text_source(s: dict, stored: str | None) -> str:
    """quoted > attributed (newsroom sentence naming its source) > stored (newsroom).

    Attributed stance is the source's position, not the outlet's (codebook 9.2, D-81).
    """
    if s["quoted"]:
        return "quoted"
    if s["attributed"]:
        return "attributed"
    return stored or "newsroom"


def load(con) -> pd.DataFrame:
    art = {
        r["id"]: r
        for r in con.execute("SELECT id, outlet, published, topic_tags, wire_group FROM articles")
    }
    lab = {}
    for r in con.execute(
        "SELECT sentence_id, label, value, score, source FROM labels WHERE source='babe'"
    ):
        lab[(r[0], r[1], r[4])] = r[3] if r[4] == "babe" else r[2]
    role = {r[0]: r[1] for r in con.execute("SELECT sentence_id, role FROM v15_sources")}
    ps = periods()
    ts = {r[0]: r[1] for r in con.execute("SELECT id, text_source FROM sentences")}
    rows = []
    for s in v15.v15_sentences(con):
        a = art[s["article_id"]]
        tags = set(json.loads(a["topic_tags"] or "[]"))
        r = {
            "sentence_id": s["id"],
            "article_id": s["article_id"],
            "outlet": a["outlet"],
            "part": s["part"],
            "topic": "bike_lane" if "bike_lane" in tags else "transit",
            "period": period_of(a["published"] or "", ps),
            "text_source": text_source(s, ts.get(s["id"])),
            "source_role": role.get(s["id"]),
            "loaded_language": lab.get((s["id"], "loaded_language", "babe")),
        }
        rows.append(r)
    return pd.DataFrame(rows)


def build(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    body = df[df.part == "body"]
    out = {
        "v15_loaded_language": rates(body, ["topic", "text_source", "outlet"], ["loaded_language"]),
    }
    quoted = body[body.source_role.notna()]
    out["v15_source_roles"] = (
        quoted.groupby(["topic", "outlet", "source_role"]).size().rename("quotes").reset_index()
    )
    out["v15_corpus"] = (
        df.groupby(["topic", "outlet"])
        .agg(articles=("article_id", "nunique"), sentences=("sentence_id", "count"))
        .reset_index()
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    df = load(con)
    TABLES.mkdir(parents=True, exist_ok=True)
    for name, t in build(df).items():
        t.to_csv(TABLES / f"{name}.csv", index=False)
    print(f"v15 analysis: {df.article_id.nunique()} articles, {len(df)} sentences -> {TABLES}")


if __name__ == "__main__":
    main()
