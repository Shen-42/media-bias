"""Tune release-matching thresholds on the dev set only (CLAUDE.md). Writes config values."""

import argparse
import itertools
import re

from common import config, db
from eval.sample import EVAL, read_csv
from eval.score import macro_f1, norm
from nlp.overlap import apply_text_source, text_source

EMBED_GRID = [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
CHAR_GRID = [0.0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]


def best_thresholds(rows: list[tuple[str, bool, float | None, float | None]]):
    """rows: (gold, quoted, sim, char). Max macro-F1; ties -> stricter thresholds."""
    best = None
    for e, c in itertools.product(EMBED_GRID, CHAR_GRID):
        cfg = {"embed_threshold": e, "char_threshold": c}
        y = [g for g, *_ in rows]
        yhat = [text_source(q, s, ch, cfg) for _, q, s, ch in rows]
        f = macro_f1(y, yhat)
        key = (f, e, c)
        if best is None or key > best:
            best = key
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    dev = [r for r in read_csv(EVAL / "dev_crash.csv") if r["set"] == "text_source"]
    sent = {
        r["id"]: r
        for r in con.execute("SELECT id, quoted, release_sim, release_char FROM sentences")
    }
    rows = [
        (
            norm(r["text_source"]),
            bool(sent[r["sentence_id"]]["quoted"]),
            sent[r["sentence_id"]]["release_sim"],
            sent[r["sentence_id"]]["release_char"],
        )
        for r in dev
        if norm(r["text_source"])
    ]
    f, e, c = best_thresholds(rows)
    path = config.ROOT / "config" / "config.toml"
    text = path.read_text()
    text = re.sub(r"embed_threshold = [\d.]+", f"embed_threshold = {e}", text)
    text = re.sub(r"char_threshold = [\d.]+", f"char_threshold = {c}", text)
    path.write_text(text)
    config.load.cache_clear()
    apply_text_source(con, config.load()["matching"])
    print(f"dev macro-F1 {f:.3f} at embed {e}, char {c} (n={len(rows)})")


if __name__ == "__main__":
    main()
