"""D-86 validation of the transit stance end model on the measurement sample.

Rows: measure_v15 `transit_random` rows outside the Snorkel pool and dev. Pass when the model's
stance rate falls inside the annotated Wilson 95% interval overall, per outlet and per
text source. Writes eval/reports/v15_endmodel_validation.csv.
"""

import argparse
import math

import pandas as pd

from analysis.aggregate_v15 import text_source
from common import db
from eval.sample import EVAL, read_csv
from eval.score import REPORTS
from nlp import v15

LABEL = "stance_transit"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def check(df: pd.DataFrame) -> pd.DataFrame:
    """df: one row per sentence with `gold`, `pred` (0/1 stance), `outlet`, `text_source`."""
    groups = [("all", "all", df)]
    groups += [("outlet", k, g) for k, g in df.groupby("outlet")]
    groups += [("text_source", k, g) for k, g in df.groupby("text_source")]
    out = []
    for by, key, g in groups:
        k, n = int(g.gold.sum()), len(g)
        lo, hi = wilson(k, n)
        pred = g.pred.mean()
        out.append(
            {
                "by": by,
                "group": key,
                "n": n,
                "gold_rate": k / n,
                "gold_lo": lo,
                "gold_hi": hi,
                "model_rate": pred,
                "inside": lo <= pred <= hi,
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    pool = {r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool='v15'")}
    dev = {r["sentence_id"] for r in read_csv(EVAL / "dev_v15.csv")}
    pred = {
        r[0]: r[1]
        for r in con.execute(
            "SELECT sentence_id, value FROM labels WHERE label=? AND source='endmodel'", (LABEL,)
        )
    }
    gold = {r["sentence_id"]: r for r in read_csv(EVAL / "measure_v15.csv")}
    stored = {r[0]: r[1] for r in con.execute("SELECT id, text_source FROM sentences")}
    rows = []
    for s in v15.v15_sentences(con):
        g = gold.get(s["id"])
        if not g or "transit_random" not in g["sample"] or s["id"] in pool | dev:
            continue
        rows.append(
            {
                "outlet": g["outlet"],
                "text_source": text_source(s, stored.get(s["id"])),
                "gold": float(g[LABEL] != "none"),
                "pred": float(pred[s["id"]] != "none"),
            }
        )
    res = check(pd.DataFrame(rows))
    res.to_csv(REPORTS / "v15_endmodel_validation.csv", index=False)
    print(res.round(3).to_string(index=False))
    print("PASS" if res.inside.all() else "FAIL")


if __name__ == "__main__":
    main()
