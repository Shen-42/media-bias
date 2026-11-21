"""Score v1.5 systems on the same test rows (D-73). Gold = annotator subagent labels (an LLM).

Headline samples: `random` for policy_frame, `random_target` for the stance labels.
Systems: lexicon (frame lexicon / stance cue LF), nli, qwen, snorkel, setfit.
A stance label has no NLI, Qwen or Snorkel vote when the sentence names no target; that is
`none` by codebook 9.2, so a missing vote there counts as `none`, not as an abstain.
Also: topic precision, source-role accuracy, and Cohen's kappa against a second annotator.
"""

import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from common import db
from eval.sample import EVAL, read_csv
from eval.score import REPORTS, bootstrap_ci, macro_f1, norm, per_class
from nlp import v15
from nlp.labeling import lfs_v15

SYSTEMS = ["lexicon", "nli", "qwen", "snorkel", "setfit"]
LEXICON = {
    "policy_frame": lfs_v15.lf_frame_lexicon,
    "stance_infrastructure": lfs_v15.lf_infra_cues,
    "stance_cyclists": lfs_v15.lf_cyclists_cues,
    "stance_transit": lfs_v15.lf_transit_cues,
}
HEADLINE = {"policy_frame": "random"} | {k: "random_target" for k in v15.TARGETS}


def in_scope(con) -> set[str]:
    """v1.5 sentence ids; eval rows from articles that left scope are dropped (D-79)."""
    return {s["id"] for s in v15.v15_sentences(con)}


def predictions(con, gold: list[dict]) -> dict[tuple[str, str, str], str]:
    sent = {
        r["id"]: dict(r) for r in con.execute("SELECT id, text, quoted, attributed FROM sentences")
    }
    stored = {
        (r[0], r[1], r[2]): r[3]
        for r in con.execute(
            "SELECT sentence_id, label, source, value FROM labels WHERE source IN"
            " ('nli','qwen','snorkel','setfit')"
        )
    }
    out = {}
    for g in gold:
        sid = g["sentence_id"]
        s = sent[sid]
        x = {"text": s["text"], "quoted": bool(s["quoted"]), "attributed": bool(s["attributed"])}
        for label in v15.LABELS:
            in_scope = label not in v15.TARGETS or v15.TARGETS[label].search(s["text"])
            for system in SYSTEMS:
                if system == "lexicon":
                    v = LEXICON[label](x)
                else:
                    v = stored.get((sid, label, system))
                if v is None and not in_scope:
                    v = "none"
                out[(sid, label, system)] = v or "abstain"
    return out


def score(gold: list[dict], preds) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary, classes = [], []
    for label in v15.LABELS:
        for system in SYSTEMS:
            for sample in ("random", "random_target", "disagreement"):
                sub = [g for g in gold if g["sample"] == sample and norm(g[label])]
                if not sub:
                    continue
                y = [norm(g[label]) for g in sub]
                yhat = [preds[(g["sentence_id"], label, system)] for g in sub]
                lo, hi = bootstrap_ci(y, yhat, macro_f1) if len(y) > 5 else (np.nan, np.nan)
                summary.append(
                    {
                        "label": label,
                        "system": system,
                        "sample": sample,
                        "headline": sample == HEADLINE[label],
                        "n": len(y),
                        "coverage": np.mean([p != "abstain" for p in yhat]),
                        "accuracy": np.mean([a == b for a, b in zip(y, yhat, strict=True)]),
                        "macro_f1": macro_f1(y, yhat),
                        "macro_f1_lo": lo,
                        "macro_f1_hi": hi,
                    }
                )
                classes += per_class(label, system, sample, y, yhat)
    return pd.DataFrame(summary), pd.DataFrame(classes)


def topic_precision(con) -> pd.DataFrame:
    import json

    tags = {
        r[0]: set(json.loads(r[1] or "[]"))
        for r in con.execute("SELECT id, topic_tags FROM articles")
    }
    gold = read_csv(EVAL / "test_v15_topic.csv")
    out = []
    for t in ("bike_lane", "transit"):
        sub = [g for g in gold if t in tags.get(g["article_id"], set()) and norm(g[t])]
        hits = [norm(g[t]) == "true" for g in sub]
        out.append(
            {"topic": t, "n_tagged": len(sub), "precision": np.mean(hits) if hits else np.nan}
        )
    return pd.DataFrame(out)


def source_roles(con) -> pd.DataFrame:
    pred = {r[0]: r[1] for r in con.execute("SELECT sentence_id, role FROM v15_sources")}
    scope = in_scope(con)
    gold = [
        g
        for g in read_csv(EVAL / "test_v15_source.csv")
        if norm(g["role"]) and g["sentence_id"] in scope
    ]
    y = [norm(g["role"]) for g in gold]
    yhat = [pred.get(g["sentence_id"], "abstain") for g in gold]
    lo, hi = bootstrap_ci(y, yhat, macro_f1) if len(y) > 5 else (np.nan, np.nan)
    return pd.DataFrame(
        [
            {
                "n": len(y),
                "accuracy": np.mean([a == b for a, b in zip(y, yhat, strict=True)]),
                "macro_f1": macro_f1(y, yhat),
                "macro_f1_lo": lo,
                "macro_f1_hi": hi,
                "pred_unknown": np.mean([p == "unknown" for p in yhat]),
                "gold_unknown": np.mean([g == "unknown" for g in y]),
            }
        ]
    )


def kappa(gold: list[dict], second: list[dict]) -> pd.DataFrame:
    by_id = {g["sentence_id"]: g for g in gold}
    out = []
    for label in v15.LABELS:
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
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    scope = in_scope(con)
    gold = [g for g in read_csv(EVAL / "test_v15.csv") if g["sentence_id"] in scope]
    summary, classes = score(gold, predictions(con, gold))
    summary.to_csv(REPORTS / "v15_metrics_summary.csv", index=False)
    classes.to_csv(REPORTS / "v15_metrics_per_class.csv", index=False)
    topic_precision(con).to_csv(REPORTS / "v15_topic_precision.csv", index=False)
    source_roles(con).to_csv(REPORTS / "v15_source_roles.csv", index=False)
    a2 = EVAL / "test_v15_annotator2.csv"
    if a2.exists():
        kappa(gold, read_csv(a2)).to_csv(REPORTS / "v15_agreement_kappa.csv", index=False)
    print(summary[summary.headline].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
