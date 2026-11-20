"""Sample test and dev sentences for the annotator subagents (PLAN.md §10, D-26, D-37).

Three sets, each with a random part (headline metrics) and, for test, a disagreement part:
- crash: crash sentences, labels voice, driver_reference, focus, vru_as_actor, accident_term
- context: body sentences of crash articles, labels vru_conduct_detail, thematic_cue
- text_source: body sentences of release-linked articles, label text_source

Committed CSVs hold IDs and labels only (D-24). Sentence text goes to data/eval/ packets.
"""

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from common import config, db

EVAL = Path(__file__).parent
CRASH_LABELS = ["voice", "driver_reference", "focus", "vru_as_actor", "accident_term"]
CONTEXT_LABELS = ["vru_conduct_detail", "thematic_cue"]
COLUMNS = (
    ["sentence_id", "set", "sample", "outlet", "year", "part"]
    + CRASH_LABELS
    + CONTEXT_LABELS
    + ["text_source", "annotator"]
)
SIZES = {
    "test": {"crash": (60, 40), "context": (60, 40), "text_source": (40, 0)},
    "dev": {"crash": (30, 0), "context": (30, 0), "text_source": (40, 0)},
}


def excluded_ids(path: Path = EVAL / "excluded_ids.txt") -> set[str]:
    out = set()
    for ln in path.read_text().splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            out.add(ln)
    return out


def is_excluded(sid: str, excl: set[str]) -> bool:
    return sid in excl or sid.split(":")[0] in excl


def stratified(cands: list[dict], n: int, rng: random.Random, excl: set[str]) -> list[dict]:
    """Proportional sample over outlet x year strata, skipping excluded IDs."""
    pool = [c for c in cands if not is_excluded(c["sentence_id"], excl)]
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for c in pool:
        strata[(c["outlet"], c["year"])].append(c)
    for v in strata.values():
        rng.shuffle(v)
    total = len(pool)
    picked: list[dict] = []
    if not total:
        return picked
    quotas = {k: n * len(v) / total for k, v in strata.items()}
    for k in sorted(strata):
        picked += strata[k][: int(quotas[k])]
    rest = [c for k in sorted(strata) for c in strata[k][int(quotas[k]) :]]
    rng.shuffle(rest)
    picked += rest[: n - len(picked)]
    return picked[:n]


def disagreement(cands: list[dict], n: int, rng: random.Random, excl: set[str]) -> list[dict]:
    """Rows where rule, NLI and Qwen disagree on at least one label, most disagreements first."""
    pool = [
        c for c in cands if c.get("n_disagree", 0) > 0 and not is_excluded(c["sentence_id"], excl)
    ]
    rng.shuffle(pool)
    pool.sort(key=lambda c: -c["n_disagree"])
    return pool[:n]


def topup(
    rows: list[dict],
    cands: dict[str, list[dict]],
    n_random: dict[str, int],
    rng: random.Random,
    excl: set[str],
    taken: set[str],
) -> tuple[list[dict], list[dict]]:
    """Drop rows no longer in scope, then refill each set's random part to its size (D-55).

    Kept rows keep their labels. New rows are random draws from the current scope, skipping
    excluded IDs and anything already taken in either split.
    """
    in_scope = {name: {c["sentence_id"] for c in cs} for name, cs in cands.items()}
    kept = [r for r in rows if r["sentence_id"] in in_scope.get(r["set"], set())]
    taken = taken | {r["sentence_id"] for r in rows}
    new: list[dict] = []
    for name, n in n_random.items():
        have = sum(r["set"] == name and r["sample"] == "random" for r in kept)
        pool = [c for c in cands[name] if c["sentence_id"] not in taken]
        for c in stratified(pool, max(n - have, 0), rng, excl):
            new.append({**c, "set": name, "sample": "random"})
            taken.add(c["sentence_id"])
    return kept, new


def candidates(con) -> dict[str, list[dict]]:
    rows = con.execute(
        "SELECT s.id, s.part, s.is_crash, s.release_sim, a.outlet, a.published, a.release_id"
        " FROM sentences s JOIN articles a ON a.id = s.article_id"
        " WHERE a.is_crash=1 AND a.is_toronto=1 AND a.article_type != 'roundup'"
        " AND (a.is_canonical=1 OR s.part='headline')"
    ).fetchall()
    out: dict[str, list[dict]] = {"crash": [], "context": [], "text_source": []}
    for r in rows:
        c = {
            "sentence_id": r["id"],
            "outlet": r["outlet"],
            "year": (r["published"] or "")[:4],
            "part": r["part"],
        }
        if r["is_crash"]:
            out["crash"].append(c)
        if r["part"] == "body":
            out["context"].append(c)
            if r["release_id"] is not None and r["release_sim"] is not None:
                out["text_source"].append(c)
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLUMNS})


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_packets(con, rows: list[dict], split: str) -> None:
    """Annotator input: id + sentence text (+ release text for text_source). Stays in data/."""
    out_dir = config.path("data/eval/x").parent
    by_set = defaultdict(list)
    for r in rows:
        s = con.execute(
            "SELECT s.text, r.text AS release FROM sentences s JOIN articles a"
            " ON a.id = s.article_id LEFT JOIN police_releases r ON r.id = a.release_id"
            " WHERE s.id=?",
            (r["sentence_id"],),
        ).fetchone()
        item = {"sentence_id": r["sentence_id"], "headline": r["part"] == "headline"}
        item["sentence"] = s["text"]
        if r["set"] == "text_source":
            item["police_release"] = s["release"]
        by_set[r["set"]].append(item)
    for name, items in by_set.items():
        with open(out_dir / f"packet_{split}_{name}.jsonl", "w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["random", "disagreement", "topup"])
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    rng = random.Random(config.load()["eval"]["seed"])
    excl = excluded_ids()
    cands = candidates(con)
    if args.stage == "random":
        taken: set[str] = set()
        for split in ("test", "dev"):
            rows = []
            for name, (n_random, _) in SIZES[split].items():
                pool = [c for c in cands[name] if c["sentence_id"] not in taken]
                for c in stratified(pool, n_random, rng, excl):
                    rows.append({**c, "set": name, "sample": "random"})
                    taken.add(c["sentence_id"])
            write_csv(EVAL / f"{split}_crash.csv", rows)
            print(split, len(rows), "random rows")
    elif args.stage == "topup":
        taken = {
            r["sentence_id"] for sp in ("test", "dev") for r in read_csv(EVAL / f"{sp}_crash.csv")
        }
        for split in ("test", "dev"):
            rows = read_csv(EVAL / f"{split}_crash.csv")
            sizes = {name: n for name, (n, _) in SIZES[split].items()}
            kept, new = topup(rows, cands, sizes, rng, excl, taken)
            taken |= {r["sentence_id"] for r in new}
            write_csv(EVAL / f"{split}_crash.csv", kept + new)
            write_packets(con, new, f"topup_{split}")
            print(f"{split}: dropped {len(rows) - len(kept)} out-of-scope rows, added {len(new)}")
        return
    else:
        from eval.triage import disagreement_counts

        rows = read_csv(EVAL / "test_crash.csv")
        taken = {r["sentence_id"] for r in rows} | {
            r["sentence_id"] for r in read_csv(EVAL / "dev_crash.csv")
        }
        counts = disagreement_counts(con)
        for name in ("crash", "context"):
            pool = [
                {**c, "n_disagree": counts.get((c["sentence_id"], name), 0)}
                for c in cands[name]
                if c["sentence_id"] not in taken
            ]
            for c in disagreement(pool, SIZES["test"][name][1], rng, excl):
                rows.append({**c, "set": name, "sample": "disagreement"})
                taken.add(c["sentence_id"])
        write_csv(EVAL / "test_crash.csv", rows)
        print("test rows with disagreement:", len(rows))
    for split in ("test", "dev"):
        write_packets(con, read_csv(EVAL / f"{split}_crash.csv"), split)


if __name__ == "__main__":
    main()
