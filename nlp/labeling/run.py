"""Labeling entry point: python -m nlp.labeling.run --steps pools nli qwen snorkel setfit.

Pools exclude every test and dev sentence, so no eval row is used to fit Snorkel or SetFit.
Only one model is loaded at a time (8 GB RAM); every output is cached in SQLite.
"""

import argparse
import random

from common import config, db
from eval.sample import EVAL, candidates, read_csv
from nlp.labeling import nli, qwen
from nlp.lexicons import CONDUCT_RE, THEMATIC_RE

POOL_CRASH = 1500
POOL_CONTEXT = 3000
FUZZY = ("vru_conduct_detail", "thematic_cue")


def eval_ids() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {"crash": set(), "context": set(), "text_source": set()}
    for split in ("test", "dev"):
        p = EVAL / f"{split}_crash.csv"
        if p.exists():
            for r in read_csv(p):
                out[r["set"]].add(r["sentence_id"])
    return out


def build_pools(con) -> None:
    rng = random.Random(config.load()["eval"]["seed"] + 1)
    ev = eval_ids()
    held = set().union(*ev.values())
    cands = candidates(con)
    crash = [c["sentence_id"] for c in cands["crash"] if c["sentence_id"] not in held]
    rng.shuffle(crash)
    texts = {r["id"]: r["text"] for r in con.execute("SELECT id, text FROM sentences")}
    ctx = [c["sentence_id"] for c in cands["context"] if c["sentence_id"] not in held]
    rng.shuffle(ctx)
    cued = [s for s in ctx if CONDUCT_RE.search(texts[s]) or THEMATIC_RE.search(texts[s])]
    plain = [s for s in ctx if s not in set(cued)]
    half = POOL_CONTEXT // 2
    ctx_pool = cued[:half] + plain[: POOL_CONTEXT - len(cued[:half])]
    con.execute("CREATE TABLE IF NOT EXISTS pools (sentence_id TEXT, pool TEXT)")
    con.execute("DELETE FROM pools")
    con.executemany("INSERT INTO pools VALUES (?, 'crash')", [(s,) for s in crash[:POOL_CRASH]])
    con.executemany("INSERT INTO pools VALUES (?, 'context')", [(s,) for s in ctx_pool])
    con.commit()
    print(f"pools: crash {min(len(crash), POOL_CRASH)}, context {len(ctx_pool)}", flush=True)


def _rows(con, pool: str, ev_set: str) -> list[tuple[str, str]]:
    ids = {r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool=?", (pool,))}
    ids |= eval_ids()[ev_set]
    return [
        (r["id"], r["text"])
        for r in con.execute("SELECT id, text FROM sentences")
        if r["id"] in ids
    ]


def step_nli(con) -> None:
    rows = [(s, t, nli.CRASH_LABELS) for s, t in _rows(con, "crash", "crash")]
    rows += [(s, t, nli.CONTEXT_LABELS) for s, t in _rows(con, "context", "context")]
    nli.run(con, rows)


def step_qwen(con) -> None:
    qwen.run(con, "crash", _rows(con, "crash", "crash"))
    qwen.run(con, "context", _rows(con, "context", "context"))


def _lf_rows(con, label: str, ids: list[str]) -> list[dict]:
    text = {r["id"]: r["text"] for r in con.execute("SELECT id, text FROM sentences")}
    votes: dict[tuple[str, str], tuple] = {}
    for r in con.execute(
        "SELECT sentence_id, source, value, score FROM labels WHERE label=? AND source IN"
        " ('nli','qwen')",
        (label,),
    ):
        votes[(r["sentence_id"], r["source"])] = (r["value"], r["score"])
    return [
        {
            "id": s,
            "text": text[s],
            "nli": votes.get((s, "nli"), (None, None))[1],
            "qwen": votes.get((s, "qwen"), (None, None))[0],
        }
        for s in ids
    ]


def step_snorkel_setfit(con, with_setfit: bool) -> None:
    import pandas as pd

    from nlp.labeling import setfit_train, snorkel_model

    pool = [r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool='context'")]
    ev = sorted(eval_ids()["context"])
    reports = config.path("eval/reports/x").parent
    for label in FUZZY:
        train_rows = _lf_rows(con, label, pool)
        eval_rows = _lf_rows(con, label, ev)
        lm, summary = snorkel_model.fit(label, train_rows)
        summary.to_csv(reports / f"lf_summary_{label}.csv", index=False)
        proba = snorkel_model.predict(lm, label, train_rows)
        ev_proba = snorkel_model.predict(lm, label, eval_rows) if eval_rows else []
        for r, p in zip(train_rows + eval_rows, list(proba) + list(ev_proba), strict=True):
            con.execute(
                "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
                (
                    r["id"],
                    label,
                    "snorkel",
                    "true" if p >= 0.5 else "false",
                    float(p),
                    "label model",
                ),
            )
        con.commit()
        if not with_setfit:
            continue
        texts, y = setfit_train.training_set([r["text"] for r in train_rows], proba)
        pd.Series(y).value_counts().to_csv(reports / f"setfit_train_counts_{label}.csv")
        model = setfit_train.train(texts, y)
        all_ctx = [(c["sentence_id"]) for c in candidates(con)["context"]] + ev
        all_ctx = sorted(set(all_ctx))
        text = {r["id"]: r["text"] for r in con.execute("SELECT id, text FROM sentences")}
        probs = setfit_train.predict(model, [text[s] for s in all_ctx])
        con.executemany(
            "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
            [
                (s, label, "setfit", "true" if p >= 0.5 else "false", p, "SetFit MiniLM")
                for s, p in zip(all_ctx, probs, strict=True)
            ],
        )
        con.commit()
        del model
        print(f"setfit {label}: trained on {len(texts)}, predicted {len(all_ctx)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument(
        "--steps",
        nargs="+",
        default=["pools", "nli", "qwen", "snorkel", "setfit"],
        choices=["pools", "nli", "qwen", "snorkel", "setfit"],
    )
    args = ap.parse_args()
    con = db.connect(args.db)
    if "pools" in args.steps:
        build_pools(con)
    if "nli" in args.steps:
        step_nli(con)
    if "qwen" in args.steps:
        step_qwen(con)
    if "snorkel" in args.steps or "setfit" in args.steps:
        step_snorkel_setfit(con, with_setfit="setfit" in args.steps)


if __name__ == "__main__":
    main()
