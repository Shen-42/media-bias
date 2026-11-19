"""Score every system on the same test rows (CLAUDE.md evaluation rules).

Headline metrics use sample == random only; disagreement rows are reported separately.
Systems: rule (grammatical labels), nli (zero-shot baseline / LF), qwen (LF),
snorkel (label model), setfit (end model). Gold = annotator subagent labels (an LLM, not a human).
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score, precision_recall_fscore_support

from common import config, db
from eval.sample import CONTEXT_LABELS, CRASH_LABELS, EVAL, read_csv
from nlp.overlap import text_source

REPORTS = EVAL / "reports"
SYSTEMS = {
    "crash": ["rule", "nli", "qwen"],
    "context": ["lexicon", "nli", "qwen", "snorkel", "setfit"],
}


def norm(v) -> str | None:
    if v is None or v == "":
        return None
    s = str(v).strip().lower()
    return {"yes": "true", "no": "false", "1": "true", "0": "false"}.get(s, s)


def bootstrap_ci(y_true, y_pred, fn, n=1000, seed=0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(y_true), len(y_true))
        vals.append(fn(y_true[idx], y_pred[idx]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def macro_f1(y_true, y_pred) -> float:
    labels = sorted(set(y_true))
    return f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)


def per_class(label: str, system: str, sample: str, y_true, y_pred) -> list[dict]:
    classes = sorted(set(y_true) | {p for p in y_pred if p != "abstain"})
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=classes, zero_division=0)
    return [
        {
            "label": label,
            "system": system,
            "sample": sample,
            "class": c,
            "precision": p[i],
            "recall": r[i],
            "f1": f[i],
            "support": int(s[i]),
        }
        for i, c in enumerate(classes)
    ]


def score(
    gold: list[dict], preds: dict[tuple[str, str, str], str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary, classes = [], []
    for set_name, labels in (("crash", CRASH_LABELS), ("context", CONTEXT_LABELS)):
        rows = [g for g in gold if g["set"] == set_name]
        for label in labels:
            for system in SYSTEMS[set_name]:
                for sample in ("random", "disagreement"):
                    sub = [g for g in rows if g["sample"] == sample and norm(g[label])]
                    if not sub:
                        continue
                    y = [norm(g[label]) for g in sub]
                    yhat = [preds.get((g["sentence_id"], label, system)) or "abstain" for g in sub]
                    covered = [i for i, p in enumerate(yhat) if p != "abstain"]
                    mf1 = macro_f1(y, yhat)
                    lo, hi = bootstrap_ci(y, yhat, macro_f1) if len(y) > 5 else (np.nan, np.nan)
                    summary.append(
                        {
                            "set": set_name,
                            "label": label,
                            "system": system,
                            "sample": sample,
                            "n": len(y),
                            "coverage": len(covered) / len(y),
                            "accuracy": np.mean([a == b for a, b in zip(y, yhat, strict=True)]),
                            "macro_f1": mf1,
                            "macro_f1_lo": lo,
                            "macro_f1_hi": hi,
                        }
                    )
                    classes += per_class(label, system, sample, y, yhat)
    return pd.DataFrame(summary), pd.DataFrame(classes)


def load_preds(con) -> dict[tuple[str, str, str], str]:
    from nlp.lexicons import CONDUCT_RE, THEMATIC_RE

    preds = {
        (r["sentence_id"], r["label"], r["source"]): norm(r["value"])
        for r in con.execute("SELECT sentence_id, label, source, value FROM labels")
    }
    for r in con.execute("SELECT id, text FROM sentences"):
        preds[(r["id"], "vru_conduct_detail", "lexicon")] = (
            "true" if CONDUCT_RE.search(r["text"]) else "false"
        )
        preds[(r["id"], "thematic_cue", "lexicon")] = (
            "true" if THEMATIC_RE.search(r["text"]) else "false"
        )
    return preds


def score_text_source(con, gold: list[dict], cfg: dict) -> pd.DataFrame:
    sent = {
        r["id"]: r
        for r in con.execute("SELECT id, quoted, release_sim, release_char FROM sentences")
    }
    out = []
    for sample in ("random",):
        sub = [g for g in gold if g["set"] == "text_source" and norm(g["text_source"])]
        if not sub:
            continue
        y = [norm(g["text_source"]) for g in sub]
        s = [sent[g["sentence_id"]] for g in sub]
        yhat = [text_source(bool(x["quoted"]), x["release_sim"], x["release_char"], cfg) for x in s]
        lo, hi = bootstrap_ci(y, yhat, macro_f1)
        out.append(
            {
                "set": "text_source",
                "label": "text_source",
                "system": "rule",
                "sample": sample,
                "n": len(y),
                "coverage": 1.0,
                "accuracy": np.mean([a == b for a, b in zip(y, yhat, strict=True)]),
                "macro_f1": macro_f1(y, yhat),
                "macro_f1_lo": lo,
                "macro_f1_hi": hi,
            }
        )
    return pd.DataFrame(out)


def kappa(gold: list[dict], second: list[dict]) -> pd.DataFrame:
    by_id = {g["sentence_id"]: g for g in gold}
    out = []
    for label in CRASH_LABELS + CONTEXT_LABELS:
        pairs = [
            (norm(by_id[s["sentence_id"]][label]), norm(s[label]))
            for s in second
            if s["sentence_id"] in by_id and norm(s[label]) and norm(by_id[s["sentence_id"]][label])
        ]
        if len(pairs) < 2:
            continue
        a, b = zip(*pairs, strict=True)
        k = cohen_kappa_score(a, b) if len(set(a) | set(b)) > 1 else float("nan")
        out.append(
            {
                "label": label,
                "n": len(pairs),
                "agreement": np.mean([x == y for x, y in pairs]),
                "cohen_kappa": k,
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default=str(EVAL / "test_crash.csv"))
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    gold = read_csv(Path(args.test))
    summary, classes = score(gold, load_preds(con))
    ts = score_text_source(con, gold, config.load()["matching"])
    REPORTS.mkdir(exist_ok=True)
    pd.concat([summary, ts]).to_csv(REPORTS / "metrics_summary.csv", index=False)
    classes.to_csv(REPORTS / "metrics_per_class.csv", index=False)
    second = EVAL / "test_crash_annotator2.csv"
    if second.exists():
        kappa(gold, read_csv(second)).to_csv(REPORTS / "agreement_kappa.csv", index=False)
    print(pd.concat([summary, ts]).query("sample == 'random'").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
