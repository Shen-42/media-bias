"""v1.5 eval samples (D-73): python -m eval.sample_v15 {sentences,disagreement}.

sentences: test = 100 random + 60 random with a stance target; dev = 60 random + 40 with a
  target; plus 60 articles for topic precision and 60 quote units for source roles (test).
disagreement: 40 test rows where SetFit and a lexicon labeling function disagree.
Nothing is drawn from the Snorkel pool or from eval/excluded_ids.txt. Packets go to data/.
"""

import argparse
import csv
import json
import random
from pathlib import Path

from common import config, db
from eval.sample import EVAL, excluded_ids, read_csv
from nlp import v15
from nlp.labeling import lfs_v15

SENT_COLS = ["sentence_id", "set", "sample", "outlet", "year", "part", *v15.LABELS, "annotator"]
TOPIC_COLS = ["article_id", "set", "sample", "outlet", "year", "bike_lane", "transit", "annotator"]
ATTRIB_COLS = ["sentence_id", "set", "sample", "outlet", "year", "part", "attributed", "annotator"]
ATTRIB_N = 150  # per split (D-91)
SOURCE_COLS = ["sentence_id", "set", "sample", "outlet", "year", "speaker", "role", "annotator"]
PACKETS = Path(config.ROOT) / "data" / "eval" / "in"


def has_target(text: str) -> bool:
    return any(rx.search(text) for rx in v15.TARGETS.values())


def draw(items: list, n: int, taken: set, rng, key=lambda x: x["id"]) -> list:
    out = []
    for it in items:
        if len(out) == n:
            break
        if key(it) not in taken:
            out.append(it)
            taken.add(key(it))
    return out


def _write(path: Path, cols: list[str], rows: list[dict]) -> None:
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def _meta(con) -> dict[str, dict]:
    return {
        r["id"]: {"outlet": r["outlet"], "year": (r["published"] or "")[:4]}
        for r in con.execute("SELECT id, outlet, published FROM articles")
    }


def _packet(name: str, lines: list[dict]) -> None:
    PACKETS.mkdir(parents=True, exist_ok=True)
    with open(PACKETS / f"packet_{name}.jsonl", "w") as f:
        for ln in lines:
            f.write(json.dumps(ln) + "\n")


def sentences(con, rng) -> None:
    pool = {r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool='v15'")}
    taken = pool | excluded_ids() | v15.eval_ids()
    sents = v15.v15_sentences(con)
    rng.shuffle(sents)
    tgt = [s for s in sents if has_target(s["text"])]
    meta = _meta(con)
    plan = {
        "test": [("random", sents, 100), ("random_target", tgt, 60)],
        "dev": [("random", sents, 60), ("target", tgt, 40)],
    }
    for split, parts in plan.items():
        rows = []
        for sample, src, n in parts:
            for s in draw(src, n, taken, rng):
                rows.append(
                    {
                        "sentence_id": s["id"],
                        "set": "sentence",
                        "sample": sample,
                        "part": s["part"],
                        **meta[s["article_id"]],
                        "text": s["text"],
                    }
                )
        _write(EVAL / f"{split}_v15.csv", SENT_COLS, rows)
        order = rows[:]
        rng.shuffle(order)
        _packet(
            f"{split}_v15",
            [
                {
                    "sentence_id": r["sentence_id"],
                    "headline": r["part"] == "headline",
                    "sentence": r["text"],
                }
                for r in order
            ],
        )
    # Topic precision: tagged articles, headline + first two paragraphs.
    arts = [
        dict(r)
        for r in con.execute(
            "SELECT id, title, text, topic_tags FROM articles WHERE is_toronto=1 AND is_canonical=1"
        )
    ]
    arts = [a for a in arts if set(json.loads(a["topic_tags"] or "[]")) & {"bike_lane", "transit"}]
    rng.shuffle(arts)
    arts = arts[:60]
    _write(
        EVAL / "test_v15_topic.csv",
        TOPIC_COLS,
        [
            {"article_id": a["id"], "set": "topic", "sample": "random", **meta[a["id"]]}
            for a in arts
        ],
    )
    _packet(
        "test_v15_topic",
        [
            {
                "article_id": a["id"],
                "headline": a["title"],
                "lead": "\n".join([p for p in (a["text"] or "").split("\n") if p.strip()][:2]),
            }
            for a in arts
        ],
    )
    # Source roles: quote units with the whole article body, so the annotator sees introductions.
    units = [
        dict(r)
        for r in con.execute(
            "SELECT q.sentence_id, s.article_id, s.text FROM v15_sources q"
            " JOIN sentences s ON s.id = q.sentence_id"
        )
    ]
    rng.shuffle(units)
    units = [u for u in units if u["sentence_id"] not in taken][:60]
    body = {a: t for a, t in con.execute("SELECT id, text FROM articles")}
    _write(
        EVAL / "test_v15_source.csv",
        SOURCE_COLS,
        [
            {
                "sentence_id": u["sentence_id"],
                "set": "source",
                "sample": "random",
                **meta[u["article_id"]],
            }
            for u in units
        ],
    )
    _packet(
        "test_v15_source",
        [
            {
                "sentence_id": u["sentence_id"],
                "sentence": u["text"],
                "article": body[u["article_id"]],
            }
            for u in units
        ],
    )
    print("v15 samples written", flush=True)


def disagreement(con, rng) -> None:
    """Rows where SetFit's label differs from a non-abstaining lexicon/cue LF."""
    taken = (
        {r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool='v15'")}
        | excluded_ids()
        | v15.eval_ids()
    )
    setfit = {
        (r[0], r[1]): r[2]
        for r in con.execute(
            "SELECT sentence_id, label, value FROM labels WHERE source='setfit' AND label IN"
            " ('policy_frame','stance_infrastructure','stance_cyclists','stance_transit')"
        )
    }
    lex = {
        "policy_frame": lfs_v15.lf_frame_lexicon,
        "stance_infrastructure": lfs_v15.lf_infra_cues,
        "stance_cyclists": lfs_v15.lf_cyclists_cues,
        "stance_transit": lfs_v15.lf_transit_cues,
    }
    sents = [s for s in v15.v15_sentences(con) if s["id"] not in taken]
    rng.shuffle(sents)
    meta = _meta(con)
    rows = []
    for s in sents:
        x = {"text": s["text"], "quoted": bool(s["quoted"]), "attributed": bool(s["attributed"])}
        if any(
            (v := lf(x)) is not None and setfit.get((s["id"], lab)) not in (None, v)
            for lab, lf in lex.items()
        ):
            rows.append(
                {
                    "sentence_id": s["id"],
                    "set": "sentence",
                    "sample": "disagreement",
                    "part": s["part"],
                    **meta[s["article_id"]],
                    "text": s["text"],
                }
            )
        if len(rows) == 40:
            break
    _write(EVAL / "test_v15.csv", SENT_COLS, rows)
    _packet(
        "dis_test_v15",
        [
            {
                "sentence_id": r["sentence_id"],
                "headline": r["part"] == "headline",
                "sentence": r["text"],
            }
            for r in rows
        ],
    )
    print(f"disagreement rows: {len(rows)}", flush=True)


MEASURE_TRANSIT = 200  # random transit-mention body sentences per outlet (D-85)
PACKET_SIZE = 100


def measure_rows(sents: list[dict], rng) -> list[tuple[dict, str]]:
    """Every body sentence naming bike infrastructure or cyclists (`census`), plus
    MEASURE_TRANSIT random transit-mention body sentences per outlet (`transit_random`).
    A sentence in both gets `census+transit_random`. `sents` carry an `outlet` key."""
    body = [s for s in sents if s["part"] == "body"]
    census = {
        s["id"]
        for s in body
        if v15.TARGETS["stance_infrastructure"].search(s["text"])
        or v15.TARGETS["stance_cyclists"].search(s["text"])
    }
    transit = [s for s in body if v15.TARGETS["stance_transit"].search(s["text"])]
    rng.shuffle(transit)
    drawn: set[str] = set()
    for outlet in sorted({s["outlet"] for s in transit}):
        mine = [s["id"] for s in transit if s["outlet"] == outlet]
        drawn |= set(mine[:MEASURE_TRANSIT])
    out = []
    for s in body:
        tags = [t for t, ids in (("census", census), ("transit_random", drawn)) if s["id"] in ids]
        if tags:
            out.append((s, "+".join(tags)))
    return out


URBANIST_CAP = 300  # per outlet (D-99): random draw when an outlet has more census rows


def measure_urbanist(con, rng) -> None:
    """Bike-infrastructure census sentences from the urbanist outlets (data/compare.sqlite),
    capped per outlet, for the same annotation as measure_v15 (D-99). One packet pass labels
    the v1.5 labels and stance_holder together."""
    meta = _meta(con)
    sents = [s | {"outlet": meta[s["article_id"]]["outlet"]} for s in v15.v15_sentences(con)]
    census = [
        s
        for s in sents
        if s["part"] == "body"
        and (
            v15.TARGETS["stance_infrastructure"].search(s["text"])
            or v15.TARGETS["stance_cyclists"].search(s["text"])
        )
    ]
    rows = []
    for outlet in sorted({s["outlet"] for s in census}):
        mine = sorted((s for s in census if s["outlet"] == outlet), key=lambda s: s["id"])
        sample = "census"
        if len(mine) > URBANIST_CAP:
            rng.shuffle(mine)
            mine, sample = mine[:URBANIST_CAP], "census_random"
        rows += [
            {"sentence_id": s["id"], "set": "measure", "sample": sample, "part": "body",
             **meta[s["article_id"]]}
            for s in mine
        ]  # fmt: skip
    path = EVAL / "measure_urbanist.csv"
    assert not path.exists(), path
    _write(path, [*SENT_COLS[:-1], "stance_holder", "annotator"], rows)
    text = {s["id"]: s["text"] for s in census}
    order = rows[:]
    rng.shuffle(order)
    for i in range(0, len(order), PACKET_SIZE):
        _packet(
            f"measure_urbanist_{i // PACKET_SIZE:02d}",
            [
                {
                    "sentence_id": r["sentence_id"],
                    "headline": False,
                    "sentence": text[r["sentence_id"]],
                }
                for r in order[i : i + PACKET_SIZE]
            ],
        )
    print(f"urbanist measure rows: {len(rows)}", flush=True)


def measure(con, rng) -> None:
    """Measurement sample (D-85): never used for tuning. Pool and eval rows are not excluded;
    model scoring on it drops pool rows (Snorkel training) and dev rows."""
    meta = _meta(con)
    sents = [s | {"outlet": meta[s["article_id"]]["outlet"]} for s in v15.v15_sentences(con)]
    rows = [
        {
            "sentence_id": s["id"],
            "set": "measure",
            "sample": sample,
            "part": s["part"],
            **meta[s["article_id"]],
        }
        for s, sample in measure_rows(sents, rng)
    ]
    path = EVAL / "measure_v15.csv"
    assert not path.exists(), path
    _write(path, SENT_COLS, rows)
    text = {s["id"]: s["text"] for s in sents}
    order = rows[:]
    rng.shuffle(order)
    for i in range(0, len(order), PACKET_SIZE):
        _packet(
            f"measure_v15_{i // PACKET_SIZE:02d}",
            [
                {
                    "sentence_id": r["sentence_id"],
                    "headline": False,
                    "sentence": text[r["sentence_id"]],
                }
                for r in order[i : i + PACKET_SIZE]
            ],
        )
    second = order[:: max(1, len(order) // PACKET_SIZE)][:PACKET_SIZE]
    _packet(
        "measure_v15_a2",
        [
            {"sentence_id": r["sentence_id"], "headline": False, "sentence": text[r["sentence_id"]]}
            for r in second
        ],
    )
    print(f"measure rows: {len(rows)}", flush=True)


def source_dev2(con, rng) -> None:
    """Quality check (2026-11-22): 80 more dev quote units for source roles; the first 60 dev
    rows were used up by D-77 tuning. Skips source eval rows and excluded ids."""
    taken = excluded_ids() | {
        r["sentence_id"]
        for f in ("dev_v15_source.csv", "test_v15_source.csv")
        for r in read_csv(EVAL / f)
    }
    units = [
        dict(r)
        for r in con.execute(
            "SELECT q.sentence_id, s.article_id, s.text FROM v15_sources q"
            " JOIN sentences s ON s.id = q.sentence_id"
        )
    ]
    rng.shuffle(units)
    units = [u for u in units if u["sentence_id"] not in taken][:80]
    meta = _meta(con)
    body = {a: t for a, t in con.execute("SELECT id, text FROM articles")}
    _write(
        EVAL / "dev_v15_source.csv",
        SOURCE_COLS,
        [
            {
                "sentence_id": u["sentence_id"],
                "set": "source",
                "sample": "random2",
                **meta[u["article_id"]],
            }
            for u in units
        ],
    )
    _packet(
        "dev_v15_source2",
        [
            {
                "sentence_id": u["sentence_id"],
                "sentence": u["text"],
                "article": body[u["article_id"]],
            }
            for u in units
        ],
    )
    print(f"source dev2: {len(units)} units", flush=True)


def topic_dev2(con, rng) -> None:
    """Quality check (2026-11-22): 80 more transit-tagged articles for dev topic precision;
    dev had 1 false positive in 24, too few to find error patterns. Skips topic eval articles."""
    taken = {
        r["article_id"]
        for f in ("dev_v15_topic.csv", "test_v15_topic.csv")
        for r in read_csv(EVAL / f)
    }
    arts = [
        dict(r)
        for r in con.execute(
            "SELECT id, title, text, topic_tags FROM articles WHERE is_toronto=1 AND is_canonical=1"
        )
        if "transit" in json.loads(r["topic_tags"] or "[]") and r["id"] not in taken
    ]
    rng.shuffle(arts)
    arts = arts[:80]
    meta = _meta(con)
    _write(
        EVAL / "dev_v15_topic.csv",
        TOPIC_COLS,
        [
            {"article_id": a["id"], "set": "topic", "sample": "transit_tagged", **meta[a["id"]]}
            for a in arts
        ],
    )
    _packet(
        "dev_v15_topic2",
        [
            {
                "article_id": a["id"],
                "headline": a["title"],
                "lead": "\n".join([p for p in (a["text"] or "").split("\n") if p.strip()][:2]),
            }
            for a in arts
        ],
    )
    print(f"topic dev2: {len(arts)} articles", flush=True)


def attribution(con, rng) -> None:
    """D-91: random non-quoted body sentences for the `attributed` rule; dev tunes, test scores.
    Skips the pool, eval rows, the measurement sample and excluded ids."""
    taken = (
        {r[0] for r in con.execute("SELECT sentence_id FROM pools WHERE pool='v15'")}
        | excluded_ids()
        | v15.eval_ids()
        | {r["sentence_id"] for r in read_csv(EVAL / "measure_v15.csv")}
    )
    sents = [s for s in v15.v15_sentences(con) if s["part"] == "body" and not s["quoted"]]
    rng.shuffle(sents)
    meta = _meta(con)
    for split in ("dev", "test"):
        rows = draw(sents, ATTRIB_N, taken, rng)
        path = EVAL / f"{split}_v15_attrib.csv"
        assert not path.exists(), path
        _write(
            path,
            ATTRIB_COLS,
            [
                {"sentence_id": s["id"], "set": "attrib", "sample": "random", "part": "body"}
                | meta[s["article_id"]]
                for s in rows
            ],
        )
        _packet(
            f"{split}_v15_attrib",
            [{"sentence_id": s["id"], "sentence": s["text"]} for s in rows],
        )
        if split == "test":
            _packet(
                "test_v15_attrib_a2",
                [{"sentence_id": s["id"], "sentence": s["text"]} for s in rows[::5]],
            )
    print("attribution samples written", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "stage",
        choices=[
            "sentences",
            "disagreement",
            "measure",
            "attribution",
            "topic_dev2",
            "source_dev2",
            "measure_urbanist",
        ],
    )
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    rng = random.Random(config.load()["eval"]["seed"] + 150)
    {
        "sentences": sentences,
        "disagreement": disagreement,
        "measure": measure,
        "attribution": attribution,
        "topic_dev2": topic_dev2,
        "source_dev2": source_dev2,
        "measure_urbanist": measure_urbanist,
    }[args.stage](con, rng)


if __name__ == "__main__":
    main()
