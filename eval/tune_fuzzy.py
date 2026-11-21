"""Tune fuzzy-label cutoffs on dev only (D-71). Writes [fuzzy] in config.

--stage nli: NLI labeling-function cutoffs (run before Snorkel).
--stage models: Snorkel and SetFit decision thresholds (run after training); relabels outputs.
Each cutoff maximizes positive-class F1 on all dev context rows; ties go to the stricter cutoff.
"""

import argparse
import re

from common import config, db
from eval.sample import EVAL, read_csv

FUZZY = ("vru_conduct_detail", "thematic_cue")
GRID = [round(0.3 + 0.05 * i, 2) for i in range(14)]  # 0.30 .. 0.95


def _f1(gold: list[bool], pred: list[bool]) -> float:
    tp = sum(g and p for g, p in zip(gold, pred, strict=True))
    fp = sum(p and not g for g, p in zip(gold, pred, strict=True))
    fn = sum(g and not p for g, p in zip(gold, pred, strict=True))
    return 0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn)


def best_cutoff(gold: list[bool], scores: list[float], grid=GRID) -> float:
    return max(grid, key=lambda t: (_f1(gold, [s >= t for s in scores]), t))


def _dev(label: str) -> dict[str, bool]:
    return {
        r["sentence_id"]: r[label] == "true"
        for r in read_csv(EVAL / "dev_crash.csv")
        if r["set"] == "context" and r[label] in ("true", "false")
    }


def _write(key: str, value: float) -> None:
    path = config.ROOT / "config" / "config.toml"
    path.write_text(re.sub(rf"{key} = [\d.]+", f"{key} = {value}", path.read_text()))
    config.load.cache_clear()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["nli", "models"], required=True)
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    sources = ["nli"] if args.stage == "nli" else ["snorkel", "setfit"]
    for label in FUZZY:
        gold = _dev(label)
        for src in sources:
            score = {
                r[0]: r[1]
                for r in con.execute(
                    "SELECT sentence_id, score FROM labels WHERE label=? AND source=?", (label, src)
                )
                if r[1] is not None
            }
            ids = [i for i in gold if i in score]
            t = best_cutoff([gold[i] for i in ids], [score[i] for i in ids])
            key = f"nli_hi_{label}" if src == "nli" else f"{src}_{label}"
            _write(key, t)
            if src != "nli":
                con.execute(
                    "UPDATE labels SET value = CASE WHEN score >= ? THEN 'true' ELSE 'false' END"
                    " WHERE label=? AND source=?",
                    (t, label, src),
                )
                con.commit()
            print(f"{key} = {t} (dev n={len(ids)}, positives={sum(gold[i] for i in ids)})")


if __name__ == "__main__":
    main()
