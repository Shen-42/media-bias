"""v1.5 steps (bike lanes and transit): python -m nlp.v15 --steps topics sources pools nli qwen
snorkel setfit.

Units follow codebook 7.2. NLI and Qwen run on a pool of POOL sentences plus the v1.5 eval rows;
Snorkel is fit on the pool; SetFit, trained on confident Snorkel labels, labels every sentence
(the v1 design, D-35). Pools never contain eval rows. One model in memory at a time.
"""

import argparse
import json
import random

from common import config, db
from eval.sample import EVAL, read_csv
from nlp import topic
from nlp.labeling import lfs_v15
from nlp.sources import article_sources

POOL = 3000
LABELS = tuple(lfs_v15.V15_LABELS)
TARGETS = {
    "stance_infrastructure": lfs_v15.INFRA_TARGET,
    "stance_cyclists": lfs_v15.CYCLIST_TARGET,
    "stance_transit": lfs_v15.TRANSIT_TARGET,
}
CONF = 0.7  # SetFit trains on Snorkel labels with max probability >= CONF
CAP = {"none": 400}  # per-class cap; other classes 200 (D-71 lesson: avoid 1:1 for rare classes)
DEFAULT_CAP = 200
SOURCES_SQL = """CREATE TABLE IF NOT EXISTS v15_sources (
    sentence_id TEXT PRIMARY KEY, speaker TEXT, role TEXT)"""


def v15_article_ids(con) -> set[str]:
    return {
        r["id"]
        for r in con.execute(
            "SELECT id, topic_tags FROM articles WHERE is_toronto=1 AND is_canonical=1"
        )
        if set(json.loads(r["topic_tags"] or "[]")) & {"bike_lane", "transit"}
    }


def v15_sentences(con) -> list[dict]:
    ids = v15_article_ids(con)
    return [
        dict(r)
        for r in con.execute(
            "SELECT id, article_id, part, idx, text, quoted, attributed FROM sentences"
            " ORDER BY article_id, part DESC, idx"
        )
        if r["article_id"] in ids
    ]


def eval_ids() -> set[str]:
    out = set()
    for f in ("test_v15.csv", "dev_v15.csv"):
        if (EVAL / f).exists():
            out |= {r["sentence_id"] for r in read_csv(EVAL / f)}
    return out


def step_topics(con) -> None:
    n = 0
    for a in con.execute("SELECT id, title, text, is_crash FROM articles").fetchall():
        tags = ["crash"] if a["is_crash"] else topic.topics(a["title"] or "", a["text"] or "")
        con.execute("UPDATE articles SET topic_tags=? WHERE id=?", (json.dumps(tags), a["id"]))
        n += bool(set(tags) & {"bike_lane", "transit"})
    con.commit()
    print(f"topics: {n} bike_lane/transit articles (any place)", flush=True)


def step_sources(con) -> None:
    con.execute(SOURCES_SQL)
    con.execute("DELETE FROM v15_sources")
    by_art: dict[str, list[dict]] = {}
    for s in v15_sentences(con):
        if s["part"] == "body":
            by_art.setdefault(s["article_id"], []).append(s)
    rows = []
    for sents in by_art.values():
        for i, speaker, role in article_sources([s["text"] for s in sents]):
            rows.append((sents[i]["id"], speaker, role))
    con.executemany("INSERT INTO v15_sources VALUES (?,?,?)", rows)
    con.commit()
    print(f"sources: {len(rows)} quote units in {len(by_art)} articles", flush=True)


def step_pools(con) -> None:
    held = eval_ids()
    sents = [s for s in v15_sentences(con) if s["id"] not in held]
    rng = random.Random(config.load()["eval"]["seed"] + 15)
    rng.shuffle(sents)
    # Half the pool mentions a stance target, so the stance LFs have something to vote on.
    tgt = [s for s in sents if any(rx.search(s["text"]) for rx in TARGETS.values())]
    rest = [s for s in sents if s not in tgt]
    pool = tgt[: POOL // 2]
    pool += rest[: POOL - len(pool)]
    con.execute("CREATE TABLE IF NOT EXISTS pools (sentence_id TEXT, pool TEXT)")
    con.execute("DELETE FROM pools WHERE pool='v15'")
    con.executemany("INSERT INTO pools VALUES (?, 'v15')", [(s["id"],) for s in pool])
    con.commit()
    print(f"pools: v15 {len(pool)} ({len(tgt[: POOL // 2])} with a stance target)", flush=True)


def _pool_rows(con) -> list[dict]:
    ids = {r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool='v15'")}
    ids |= eval_ids()
    return [s for s in v15_sentences(con) if s["id"] in ids]


def labels_for(text: str) -> list[str]:
    """policy_frame always; a stance label only when its target is mentioned."""
    return ["policy_frame"] + [lab for lab, rx in TARGETS.items() if rx.search(text)]


def step_nli(con) -> None:
    from nlp.labeling.nli import NLI, decide

    model = NLI(con)
    rows = _pool_rows(con)
    for n, s in enumerate(rows):
        for label in labels_for(s["text"]):
            scores = model.scores(s["id"], s["text"], label)
            value, score = decide(label, scores)
            con.execute(
                "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
                (s["id"], label, "nli", value, score, json.dumps(scores)),
            )
        if n % 200 == 0:
            con.commit()
            print(f"nli v15 {n}/{len(rows)}", flush=True)
    con.commit()


def step_qwen(con) -> None:
    from nlp.labeling import qwen

    qwen.run(con, "v15", [(s["id"], s["text"]) for s in _pool_rows(con)])


def step_babe(con) -> None:
    """Loaded-language score for every v1.5 sentence (codebook 9.3; a feature, not a label)."""
    from transformers import pipeline

    from nlp.device import get_device

    m = config.load()["models"]["babe"]
    clf = pipeline(
        "text-classification", model=m["name"], revision=m["revision"], device=get_device()
    )
    sents = v15_sentences(con)
    biased = _biased_label(clf.model.config.id2label)
    for i in range(0, len(sents), 256):
        chunk = sents[i : i + 256]
        outs = clf([s["text"] for s in chunk], top_k=None, truncation=True, batch_size=32)
        con.executemany(
            "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
            [
                (s["id"], "loaded_language", "babe", None, _score(o, biased), m["name"])
                for s, o in zip(chunk, outs, strict=True)
            ],
        )
        con.commit()
        print(f"babe {i}/{len(sents)}", flush=True)


def _biased_label(id2label: dict) -> str:
    names = {int(k): v for k, v in id2label.items()}
    for v in names.values():
        if v.lower() in ("biased", "bias"):
            return v
    return names[1]  # LABEL_1 is the biased class in the BABE data (0 = non-biased)


def _score(out: list[dict], biased: str) -> float:
    return next(float(o["score"]) for o in out if o["label"] == biased)


def lf_inputs(con, label: str, sents: list[dict]) -> list[dict]:
    votes: dict[tuple[str, str], tuple] = {}
    for r in con.execute(
        "SELECT sentence_id, source, value, evidence FROM labels WHERE label=?"
        " AND source IN ('nli','qwen')",
        (label,),
    ):
        votes[(r["sentence_id"], r["source"])] = (r["value"], r["evidence"])
    out = []
    for s in sents:
        nli_ev = votes.get((s["id"], "nli"), (None, None))[1]
        out.append(
            {
                "id": s["id"],
                "text": s["text"],
                "quoted": bool(s["quoted"]),
                "attributed": bool(s["attributed"]),
                "nli": json.loads(nli_ev) if nli_ev else None,
                "qwen": votes.get((s["id"], "qwen"), (None, None))[0],
            }
        )
    return out


def label_matrix(label: str, rows: list[dict]):
    import numpy as np

    values = lfs_v15.V15_LABELS[label]
    return np.array(
        [
            [values.index(v) if (v := lf(r)) is not None else -1 for lf in lfs_v15.LFS[label]]
            for r in rows
        ],
        dtype=int,
    )


def training_set(texts, proba, values, seed: int = 0) -> tuple[list[str], list[int]]:
    """Confident Snorkel labels, capped per class (none: CAP['none'], others DEFAULT_CAP)."""
    rng = random.Random(seed)
    by_cls: dict[int, list[str]] = {}
    for t, p in zip(texts, proba, strict=True):
        k = max(range(len(p)), key=lambda j: p[j])
        if p[k] >= CONF:
            by_cls.setdefault(k, []).append(t)
    xs, ys = [], []
    for k, ts in sorted(by_cls.items()):
        rng.shuffle(ts)
        ts = ts[: CAP.get(values[k], DEFAULT_CAP)]
        xs += ts
        ys += [k] * len(ts)
    return xs, ys


def step_snorkel_setfit(con, with_setfit: bool) -> None:
    from snorkel.labeling.model import LabelModel

    from nlp.labeling import setfit_train

    pool_ids = {r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool='v15'")}
    allsents = v15_sentences(con)
    held = eval_ids()
    for label in LABELS:
        values = lfs_v15.V15_LABELS[label]
        rx = TARGETS.get(label)
        scope = [s for s in allsents if rx is None or rx.search(s["text"])]
        train = lf_inputs(con, label, [s for s in scope if s["id"] in pool_ids])
        ev = lf_inputs(con, label, [s for s in scope if s["id"] in held])
        lm = LabelModel(cardinality=len(values), verbose=False)
        lm.fit(label_matrix(label, train), n_epochs=500, seed=0, log_freq=1000)
        rows = train + ev
        proba = lm.predict_proba(label_matrix(label, rows)) if rows else []
        con.executemany(
            "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
            [
                (r["id"], label, "snorkel", values[int(p.argmax())], float(p.max()), "label model")
                for r, p in zip(rows, proba, strict=True)
            ],
        )
        con.commit()
        if not with_setfit:
            continue
        xs, ys = training_set([r["text"] for r in train], proba[: len(train)], values)
        print(f"setfit {label}: train counts {_counts(ys, values)}", flush=True)
        model = setfit_train.train(xs, ys)
        probs = model.predict_proba([s["text"] for s in scope], batch_size=64)
        classes = sorted(set(ys))
        out = []
        for s, p in zip(scope, probs, strict=True):
            j = int(p.argmax())
            out.append((s["id"], label, "setfit", values[classes[j]], float(p[j]), "SetFit"))
        # Out of scope for a stance label: no target mentioned, so `none` (codebook 9.2).
        ids = {s["id"] for s in scope}
        out += [
            (s["id"], label, "setfit", "none", 1.0, "no target")
            for s in allsents
            if s["id"] not in ids
        ]
        con.executemany("INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)", out)
        con.commit()
        del model


def _counts(ys, values) -> dict[str, int]:
    return {values[k]: ys.count(k) for k in sorted(set(ys))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--steps", nargs="+", required=True)
    args = ap.parse_args()
    con = db.connect(args.db)
    for st in args.steps:
        if st == "snorkel":
            step_snorkel_setfit(con, with_setfit="setfit" in args.steps)
        elif st != "setfit":
            globals()[f"step_{st}"](con)


if __name__ == "__main__":
    main()
