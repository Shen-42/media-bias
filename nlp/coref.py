"""Coreference for driver and VRU mentions (codebook §1.2, §4.1; D-25: FCoref).

A cluster is a driver cluster if any mention contains a driver noun ("the driver", "a man
driving an SUV"), and a VRU cluster if any mention contains a VRU noun. Each sentence gets
driver_mention (yes/no) and is_vru, from the role nouns themselves or a linked mention.
"""

import argparse
import re

import spacy

from common import config, db
from nlp.device import get_device
from nlp.sentences import clean_body, split

DRIVER_RE = re.compile(r"\b(?:driver|motorist|operator|trucker)s?\b|\bdriving\b", re.I)
VRU_RE = re.compile(r"\b(?:pedestrian|cyclist|bicyclist|e-?biker|scooter rider)s?\b", re.I)


def sentence_flags(
    sents: list[dict], clusters: list[list[tuple[int, int]]], body: str
) -> list[dict]:
    """Return per-sentence {'driver': bool, 'vru': bool, 'driver_ev': str} for body sentences."""
    flags = [
        {
            "driver": bool(DRIVER_RE.search(s["text"])),
            "vru": bool(VRU_RE.search(s["text"])),
            "driver_ev": "role noun" if DRIVER_RE.search(s["text"]) else "",
        }
        for s in sents
    ]
    for cl in clusters:
        texts = [body[a:b] for a, b in cl]
        is_driver = any(DRIVER_RE.search(t) for t in texts)
        is_vru = any(VRU_RE.search(t) for t in texts)
        if not (is_driver or is_vru):
            continue
        for a, b in cl:
            for i, s in enumerate(sents):
                if s["start"] <= a < s["end"]:
                    if is_driver and not flags[i]["driver"]:
                        flags[i]["driver"] = True
                        flags[i]["driver_ev"] = f"coref: '{body[a:b]}'"
                    if is_vru:
                        flags[i]["vru"] = True
    return flags


def main() -> None:
    from fastcoref import FCoref

    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    cfg = config.load()
    con = db.connect(args.db)
    nlp_sm = spacy.load(cfg["models"]["spacy"]["fast"])
    model = FCoref(device=get_device())
    arts = con.execute(
        "SELECT id, title, text FROM articles WHERE is_crash=1 AND is_toronto=1"
    ).fetchall()
    for n, a in enumerate(arts):
        body = clean_body(a["title"], a["text"])
        sents = [s for s in split(nlp_sm, None, body)]
        clusters = model.predict(texts=[body])[0].get_clusters(as_strings=False) if body else []
        flags = sentence_flags(sents, clusters, body)
        for s, f in zip(sents, flags, strict=True):
            sid = f"{a['id']}:b:{s['idx']}"
            con.execute("UPDATE sentences SET is_vru=? WHERE id=?", (int(f["vru"]), sid))
            con.execute(
                "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
                (sid, "driver_mention", "rule", str(f["driver"]).lower(), None, f["driver_ev"]),
            )
        title = a["title"] or ""
        con.execute(
            "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
            (
                f"{a['id']}:h:0",
                "driver_mention",
                "rule",
                str(bool(DRIVER_RE.search(title))).lower(),
                None,
                "role noun",
            ),
        )
        con.commit()
        if n % 100 == 0:
            print(f"coref {n}/{len(arts)}", flush=True)
    print(f"coref done: {len(arts)}", flush=True)


if __name__ == "__main__":
    main()
