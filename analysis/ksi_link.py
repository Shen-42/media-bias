"""Link v1 crash articles to Toronto Police KSI collision records (D-95).

KSI = Motor Vehicle Collisions involving Killed or Seriously Injured Persons, City of Toronto
Open Data (Open Government Licence - Toronto). Only collisions with a pedestrian or cyclist
(v1 scope) in the corpus window are used.

An initial Toronto crash report matches a collision when it was published 0-2 days after the
collision and its text names the collision's first street and, if the record has one, a cross
street. The rule was fixed before looking at results; ties go to the closest date.

Outputs (aggregates only):
  analysis/tables/ksi_coverage.csv   share of KSI collisions with at least one initial report
  eval/reports/ksi_label_check.csv   article severity and road users against police records

    python -m analysis.ksi_link
"""

import json
import re
from pathlib import Path

import pandas as pd

from common import db
from eval.validate_endmodel import wilson

ROOT = Path(__file__).resolve().parent.parent
KSI = ROOT / "data" / "external" / "ksi" / "ksi.csv"
COVERAGE = ROOT / "analysis" / "tables" / "ksi_coverage.csv"
CHECK = ROOT / "eval" / "reports" / "ksi_label_check.csv"
WINDOW = ("2023-01-01", "2026-10-31")
MAX_LAG_DAYS = 2

SUFFIX = {
    "ST", "AVE", "AV", "RD", "BLVD", "DR", "CRES", "CRT", "CT", "PKWY", "LANE", "LN", "WAY",
    "CIR", "TER", "TERR", "GDNS", "PL", "SQ", "TRL", "GATE", "HTS", "PK", "PARK", "GRV", "E",
    "W", "N", "S", "EAST", "WEST", "NORTH", "SOUTH",
}  # fmt: skip


def street_pattern(name) -> re.Pattern | None:
    """'LAKE SHORE BLVD W' -> /\\blake\\s*shore\\b/i. None for blank or generic names."""
    if not isinstance(name, str) or not name.strip():
        return None
    words = name.upper().split()
    while len(words) > 1 and words[-1] in SUFFIX:
        words.pop()
    if not words or (len(words) == 1 and words[0] in SUFFIX):
        return None
    return re.compile(r"\b" + r"\s*".join(map(re.escape, words)) + r"\b", re.I)


def collisions(ksi: pd.DataFrame) -> pd.DataFrame:
    """One row per pedestrian or cyclist collision in the window."""
    k = ksi.copy()
    k["date"] = pd.to_datetime(k.accdate, errors="coerce").dt.normalize()
    k = k[(k.date >= WINDOW[0]) & (k.date <= WINDOW[1])]
    k["ped"] = k.road_user.eq("pedestrian") | k.pedestrian.astype(str).eq("True")
    k["cyc"] = k.road_user.eq("cyclist") | k.cyclist.astype(str).eq("True")
    k["fatal"] = k.injury.eq("Fatal") | k.acclass.eq("Fatal Injury")
    c = k.groupby("collision_id").agg(
        date=("date", "first"),
        st1=("stname1", "first"),
        st2=("stname2", "first"),
        st3=("stname3", "first"),
        ped=("ped", "any"),
        cyc=("cyc", "any"),
        fatal=("fatal", "any"),
    )
    return c[c.ped | c.cyc].reset_index()


def matches(text: str, row) -> bool:
    p1 = street_pattern(row.st1)
    if p1 is None or not p1.search(text):
        return False
    cross = [p for p in (street_pattern(row.st2), street_pattern(row.st3)) if p]
    return not cross or any(p.search(text) for p in cross)


def link(articles: pd.DataFrame, cols: pd.DataFrame) -> pd.DataFrame:
    """(article id, collision id) for each article that matches a collision."""
    out = []
    for a in articles.itertuples():
        lag = (a.date - cols.date).dt.days
        cand = cols[(lag >= 0) & (lag <= MAX_LAG_DAYS)]
        hits = [(abs((a.date - r.date).days), r.collision_id) for r in cand.itertuples()]
        hits = [h for h, r in zip(hits, cand.itertuples(), strict=True) if matches(a.text, r)]
        if hits:
            out.append({"article_id": a.id, "collision_id": min(hits)[1]})
    return pd.DataFrame(out, columns=["article_id", "collision_id"])


def rate_row(group: str, value: str, k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"group": group, "value": value, "covered": k, "n": n,
            "rate": k / n if n else float("nan"), "ci_lo": lo, "ci_hi": hi}  # fmt: skip


def coverage(cols: pd.DataFrame, linked: pd.DataFrame) -> pd.DataFrame:
    c = cols.assign(covered=cols.collision_id.isin(linked.collision_id))
    c["mode"] = c.ped.map({True: "pedestrian", False: "cyclist"})
    c["severity"] = c.fatal.map({True: "fatal", False: "serious_injury"})
    c["year"] = c.date.dt.year.astype(str)
    rows = [rate_row("all", "all", int(c.covered.sum()), len(c))]
    for g in ("severity", "mode", "year"):
        for v, sub in c.groupby(g):
            rows.append(rate_row(g, v, int(sub.covered.sum()), len(sub)))
    return pd.DataFrame(rows)


def label_check(arts: pd.DataFrame, cols: pd.DataFrame, linked: pd.DataFrame) -> pd.DataFrame:
    m = linked.merge(arts, left_on="article_id", right_on="id").merge(cols, on="collision_id")
    users = m.road_users.map(lambda s: set(json.loads(s or "[]")))
    checks = {
        "severity_fatal": (m.severity.eq("fatal"), m.fatal),
        "road_user_pedestrian": (users.map(lambda u: "pedestrian" in u), m.ped),
        "road_user_cyclist": (users.map(lambda u: "cyclist" in u), m.cyc),
    }
    rows = []
    for name, (pred, gold) in checks.items():
        agree = int((pred == gold).sum())
        lo, hi = wilson(agree, len(m))
        rows.append({
            "check": name, "n_articles": len(m), "agree": agree, "agreement": agree / len(m),
            "ci_lo": lo, "ci_hi": hi, "article_yes_police_no": int((pred & ~gold).sum()),
            "article_no_police_yes": int((~pred & gold).sum()),
        })  # fmt: skip
    return pd.DataFrame(rows)


def crash_articles(con) -> pd.DataFrame:
    a = pd.read_sql_query(
        "SELECT id, published, text, severity, road_users FROM articles "
        "WHERE is_crash = 1 AND is_toronto = 1 AND article_type = 'initial'",
        con,
    )
    a["date"] = pd.to_datetime(a.published.str[:10])
    return a


def main() -> None:
    cols = collisions(pd.read_csv(KSI, low_memory=False))
    arts = crash_articles(db.connect())
    linked = link(arts, cols)
    linked.to_csv(ROOT / "data" / "external" / "ksi" / "links.csv", index=False)
    cov = coverage(cols, linked)
    chk = label_check(arts, cols, linked)
    cov.to_csv(COVERAGE, index=False)
    chk.to_csv(CHECK, index=False)
    print(f"{len(cols)} KSI collisions, {len(arts)} initial reports, {len(linked)} linked")
    print(cov.round(3).to_string(index=False))
    print(chk.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
