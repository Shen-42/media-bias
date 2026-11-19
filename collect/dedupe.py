"""Near-duplicate detection for wire copy (PLAN.md §6 step 6; DECISIONS.md D-34).

Articles whose bodies share >= THRESHOLD Jaccard similarity (5-word shingles, MinHash LSH)
form a wire group. The earliest article is canonical; body sentences of the others are not
counted at corpus level. Per-outlet rates may include them (reported with and without wire).
"""

import argparse
import re

from datasketch import MinHash, MinHashLSH

from common import db

THRESHOLD = 0.7
NUM_PERM = 128


def shingles(text: str, k: int = 5) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(words[i : i + k]) for i in range(max(0, len(words) - k + 1))}


def minhash(text: str) -> MinHash:
    m = MinHash(num_perm=NUM_PERM, seed=1)
    for s in shingles(text):
        m.update(s.encode())
    return m


def groups(docs: list[tuple[str, str, str]]) -> dict[str, str]:
    """docs: (id, published, text) -> {id: group_id}, group_id = canonical (earliest) id."""
    lsh = MinHashLSH(threshold=THRESHOLD, num_perm=NUM_PERM)
    hashes = {}
    for doc_id, _, text in docs:
        if len(shingles(text)) < 20:
            continue
        hashes[doc_id] = minhash(text)
        lsh.insert(doc_id, hashes[doc_id])
    order = {d[0]: (d[1] or "", d[0]) for d in docs}
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    for doc_id, h in hashes.items():
        for other in lsh.query(h):
            if other != doc_id and hashes[other].jaccard(h) >= THRESHOLD:
                a, b = find(doc_id), find(other)
                if a != b:
                    first, second = sorted([a, b], key=lambda x: order[x])
                    parent[second] = first
    return {d: find(d) for d in hashes if find(d) != d or d in parent.values()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    docs = [
        (r["id"], r["published"], r["text"] or "")
        for r in con.execute("SELECT id, published, text FROM articles WHERE is_crash=1")
    ]
    g = groups(docs)
    con.execute("UPDATE articles SET wire_group=NULL, is_canonical=1")
    for doc_id, gid in g.items():
        con.execute(
            "UPDATE articles SET wire_group=?, is_canonical=? WHERE id=?",
            (gid, int(doc_id == gid), doc_id),
        )
    con.commit()
    print(f"dedupe: {len(g)} articles in {len(set(g.values()))} wire groups", flush=True)


if __name__ == "__main__":
    main()
