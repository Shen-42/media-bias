"""Score the French crash rules against annotator labels (D-101).

Crash detection: precision and recall of the rule's crash-sentence call. Labels: accuracy
and macro-F1 on sentences both the rule and the annotator call crash sentences.

    python -m eval.score_fr --split test --db data/cities.sqlite
"""

import argparse
import csv

import pandas as pd
from sklearn.metrics import f1_score

from common import config, db
from eval.sample_fr import FIELDS
from eval.validate_endmodel import wilson

EVAL = config.ROOT / "eval"


def score(gold: pd.DataFrame, pred: pd.DataFrame) -> pd.DataFrame:
    m = gold.merge(pred, on="sentence_id", suffixes=("", "_rule"))
    gold_crash = m.voice != "not_crash"
    tp = int((gold_crash & m.is_crash).sum())
    rows = []
    for name, k, n in (("crash_precision", tp, int(m.is_crash.sum())),
                       ("crash_recall", tp, int(gold_crash.sum()))):  # fmt: skip
        lo, hi = wilson(k, n)
        rows.append({"label": name, "n": n, "value": k / n if n else float("nan"),
                     "ci_lo": lo, "ci_hi": hi, "macro_f1": float("nan")})  # fmt: skip
    both = m[gold_crash & m.is_crash]
    for f in FIELDS:
        g, p = both[f].astype(str).str.lower(), both[f"{f}_rule"].astype(str).str.lower()
        k = int((g == p).sum())
        lo, hi = wilson(k, len(both))
        rows.append({
            "label": f, "n": len(both), "value": k / len(both) if len(both) else float("nan"),
            "ci_lo": lo, "ci_hi": hi,
            "macro_f1": f1_score(g, p, average="macro", zero_division=0)
            if len(both) else float("nan"),
        })  # fmt: skip
    return pd.DataFrame(rows)


def rule_labels(con, ids: list[str]) -> pd.DataFrame:
    q = ",".join("?" * len(ids))
    s = pd.read_sql(f"SELECT id AS sentence_id, is_crash FROM sentences WHERE id IN ({q})", con,
                    params=ids)  # fmt: skip
    lab = pd.read_sql(
        "SELECT sentence_id, label, value FROM labels WHERE source='rule'"
        f" AND sentence_id IN ({q})",
        con,
        params=ids,
    )
    lab = lab.pivot_table(index="sentence_id", columns="label", values="value", aggfunc="first")
    out = s.merge(lab, left_on="sentence_id", right_index=True, how="left")
    out["is_crash"] = out.is_crash.astype(bool)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--db", default="data/cities.sqlite")
    args = ap.parse_args()
    gold = pd.DataFrame(list(csv.DictReader(open(EVAL / f"{args.split}_crash_fr.csv"))))
    gold = gold[gold.voice.fillna("") != ""]
    pred = rule_labels(db.connect(args.db), gold.sentence_id.tolist())
    out = score(gold, pred)
    out.to_csv(EVAL / "reports" / f"fr_{args.split}_metrics.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
