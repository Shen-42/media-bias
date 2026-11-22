"""Dev and test samples for the French crash rules (D-101).

Draws random sentences that match the French candidate filter from in-city Radio-Canada
crash-candidate articles, so the sample holds both crash and non-crash sentences, as the
English test set does. Writes ID-only CSVs (labels filled by eval.merge_labels-style merge)
and text packets in data/eval/in for the annotator subagent.

    python -m eval.sample_fr --db data/cities.sqlite
    python -m eval.sample_fr --merge test data/eval/out/test_crash_fr.jsonl
    python -m eval.sample_fr --merge test data/eval/out/test_crash_fr_a2.jsonl --second
"""

import argparse
import csv
import json
import random

from common import config, db
from nlp.rules_fr import CANDIDATE_RE

EVAL = config.ROOT / "eval"
PACKETS = config.ROOT / "data" / "eval" / "in"
FIELDS = ["voice", "driver_reference", "focus", "vru_as_actor", "accident_term"]
SIZES = {"dev": 30, "test": 80}


def candidates(con) -> list[dict]:
    rows = con.execute(
        "SELECT s.id, s.text, s.part FROM sentences s JOIN articles a ON a.id = s.article_id"
        " WHERE a.outlet = 'radiocanada' AND a.is_toronto = 1"
        " AND EXISTS (SELECT 1 FROM sentences c WHERE c.article_id = a.id AND c.is_crash = 1)"
    ).fetchall()
    return [dict(r) for r in rows if CANDIDATE_RE.search(r["text"])]


def draw(rows: list[dict], seed: int = 101) -> dict[str, list[dict]]:
    rows = sorted(rows, key=lambda r: r["id"])
    random.Random(seed).shuffle(rows)
    out, i = {}, 0
    for split, n in SIZES.items():
        out[split] = rows[i : i + n]
        i += n
    return out


def merge(split: str, labels_path: str, second: bool = False) -> int:
    """Copy annotator labels into the split CSV (or a second-annotator CSV)."""
    rows = list(csv.DictReader(open(EVAL / f"{split}_crash_fr.csv")))
    got = {}
    for line in open(labels_path):
        d = json.loads(line)
        got[d["sentence_id"]] = {f: str(d[f]).lower() for f in FIELDS}
    if second:
        rows = [r for r in rows if r["sentence_id"] in got]
    for r in rows:
        r.update(got[r["sentence_id"]], annotator="claude-subagent")
    out = EVAL / (f"{split}_crash_fr_annotator2.csv" if second else f"{split}_crash_fr.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, ["sentence_id", "sample", "part", *FIELDS, "annotator"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/cities.sqlite")
    ap.add_argument("--merge", nargs=2, metavar=("SPLIT", "LABELS"))
    ap.add_argument("--second", action="store_true")
    args = ap.parse_args()
    if args.merge:
        print("merged", merge(*args.merge, second=args.second))
        return
    samples = draw(candidates(db.connect(args.db)))
    PACKETS.mkdir(parents=True, exist_ok=True)
    for split, rows in samples.items():
        with open(EVAL / f"{split}_crash_fr.csv", "w", newline="") as f:
            w = csv.DictWriter(f, ["sentence_id", "sample", "part", *FIELDS, "annotator"])
            w.writeheader()
            for r in rows:
                w.writerow({"sentence_id": r["id"], "sample": "random", "part": r["part"]})
        with open(PACKETS / f"packet_{split}_crash_fr.jsonl", "w") as f:
            for r in rows:
                rec = {"sentence_id": r["id"], "headline": r["part"] == "headline"}
                f.write(json.dumps({**rec, "sentence": r["text"]}, ensure_ascii=False) + "\n")
        print(split, len(rows))


if __name__ == "__main__":
    main()
