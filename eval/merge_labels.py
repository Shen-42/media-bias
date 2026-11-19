"""Merge annotator JSONL output into the eval CSVs (annotator = claude-subagent).

Usage: python -m eval.merge_labels <split> <set> <labels.jsonl> [--second]
--second writes the second annotator's rows to eval/test_crash_annotator2.csv.
"""

import argparse
import json
from pathlib import Path

from eval.sample import COLUMNS, EVAL, read_csv, write_csv

FIELDS = {
    "crash": ["voice", "driver_reference", "focus", "vru_as_actor", "accident_term"],
    "context": ["vru_conduct_detail", "thematic_cue"],
    "text_source": ["text_source"],
}
ALLOWED = {
    "voice": {"active", "passive_with_agent", "agentless_passive", "intransitive", "nominal"},
    "driver_reference": {"person", "vehicle", "absent"},
    "focus": {"vru", "driver", "vehicle", "other"},
    "vru_as_actor": {"true", "false"},
    "accident_term": {"true", "false"},
    "vru_conduct_detail": {"true", "false"},
    "thematic_cue": {"true", "false"},
    "text_source": {"quoted", "police_matched", "newsroom"},
}


def clean(field: str, value) -> str:
    v = str(value).strip().lower()
    if v == "not_crash" and field in FIELDS["crash"]:
        return v
    if v not in ALLOWED[field]:
        raise ValueError(f"{field}: invalid label {value!r}")
    return v


def merge(rows: list[dict], set_name: str, labels: list[dict]) -> int:
    by_id = {r["sentence_id"]: r for r in rows if r["set"] == set_name}
    n = 0
    for lab in labels:
        row = by_id.get(lab["sentence_id"])
        if row is None:
            raise KeyError(f"unknown sentence_id {lab['sentence_id']}")
        for f in FIELDS[set_name]:
            row[f] = clean(f, lab[f])
        row["annotator"] = "claude-subagent"
        n += 1
    missing = [i for i, r in by_id.items() if not r.get(FIELDS[set_name][0])]
    if missing:
        raise ValueError(f"{len(missing)} rows still unlabeled, e.g. {missing[0]}")
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("split", choices=["test", "dev"])
    ap.add_argument("set", choices=list(FIELDS))
    ap.add_argument("labels")
    ap.add_argument("--second", action="store_true")
    args = ap.parse_args()
    labels = [json.loads(x) for x in Path(args.labels).read_text().splitlines() if x.strip()]
    main_csv = EVAL / f"{args.split}_crash.csv"
    if args.second:
        out = EVAL / "test_crash_annotator2.csv"
        base = read_csv(out) if out.exists() else []
        ids = {r["sentence_id"] for r in base}
        src = {r["sentence_id"]: r for r in read_csv(main_csv)}
        for lab in labels:
            if lab["sentence_id"] not in ids:
                r = {k: src[lab["sentence_id"]].get(k, "") for k in COLUMNS}
                for f in FIELDS["crash"] + FIELDS["context"] + FIELDS["text_source"]:
                    r[f] = ""
                base.append(r)
        sub = [r for r in base if r["set"] == args.set]
        for lab in labels:
            row = next(r for r in sub if r["sentence_id"] == lab["sentence_id"])
            for f in FIELDS[args.set]:
                row[f] = clean(f, lab[f])
            row["annotator"] = "claude-subagent-2"
        write_csv(out, base)
        print(f"annotator 2: {len(labels)} rows -> {out}")
        return
    rows = read_csv(main_csv)
    n = merge(rows, args.set, labels)
    write_csv(main_csv, rows)
    print(f"merged {n} {args.set} labels into {main_csv}")


if __name__ == "__main__":
    main()
