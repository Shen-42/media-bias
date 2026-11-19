"""Police-release overlap and text_source (codebook §3.1, §4.4; PLAN.md §8.2).

For each sentence of an article linked to a release: max cosine similarity (all-mpnet-base-v2)
and max character 5-gram Jaccard against the release's sentences. text_source is derived with
precedence quoted > police_matched > newsroom, using thresholds tuned on the dev set only.
"""

import argparse
import re

from common import config, db
from nlp.device import get_device


def char_ngrams(text: str, n: int = 5) -> set[str]:
    t = re.sub(r"\s+", " ", text.lower())
    return {t[i : i + n] for i in range(max(0, len(t) - n + 1))}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def text_source(quoted: bool, sim: float | None, char: float | None, cfg: dict) -> str:
    if quoted:
        return "quoted"
    if sim is not None and sim >= cfg["embed_threshold"] and (char or 0) >= cfg["char_threshold"]:
        return "police_matched"
    return "newsroom"


def split_release(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [p.strip() for p in parts if len(p.strip()) > 20]


def score_sentences(model, sents: list[str], release_sents: list[str]) -> list[tuple[float, float]]:
    if not release_sents or not sents:
        return [(None, None)] * len(sents)
    a = model.encode(sents, normalize_embeddings=True, convert_to_numpy=True)
    b = model.encode(release_sents, normalize_embeddings=True, convert_to_numpy=True)
    sims = (a @ b.T).max(axis=1)
    rel_grams = [char_ngrams(r) for r in release_sents]
    chars = [max(jaccard(char_ngrams(s), g) for g in rel_grams) for s in sents]
    return [(float(s), float(c)) for s, c in zip(sims, chars, strict=True)]


def apply_text_source(con, cfg: dict) -> None:
    rows = con.execute("SELECT id, quoted, release_sim, release_char FROM sentences").fetchall()
    con.executemany(
        "UPDATE sentences SET text_source=? WHERE id=?",
        [
            (text_source(bool(r["quoted"]), r["release_sim"], r["release_char"], cfg), r["id"])
            for r in rows
        ],
    )
    con.commit()


def main() -> None:
    from sentence_transformers import SentenceTransformer

    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    cfg = config.load()
    con = db.connect(args.db)
    m = cfg["models"]["embed"]
    model = SentenceTransformer(m["name"], revision=m["revision"], device=get_device())
    arts = con.execute(
        "SELECT a.id, r.text FROM articles a JOIN police_releases r ON r.id = a.release_id"
        " WHERE a.is_crash=1 AND a.is_toronto=1"
    ).fetchall()
    for a in arts:
        rows = con.execute(
            "SELECT id, text FROM sentences WHERE article_id=?", (a["id"],)
        ).fetchall()
        scores = score_sentences(model, [r["text"] for r in rows], split_release(a["text"]))
        con.executemany(
            "UPDATE sentences SET release_sim=?, release_char=? WHERE id=?",
            [(s, c, r["id"]) for (s, c), r in zip(scores, rows, strict=True)],
        )
    con.commit()
    apply_text_source(con, cfg["matching"])
    print(f"overlap: scored {len(arts)} linked articles", flush=True)


if __name__ == "__main__":
    main()
