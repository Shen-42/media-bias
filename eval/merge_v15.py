"""Merge v1.5 annotator JSONL into eval CSVs (annotator = claude-subagent).

Usage: python -m eval.merge_v15 {test_v15,dev_v15,measure_v15,...} labels.jsonl
       [--second]   (second annotator on <name> rows -> <name>_annotator2.csv)
"""

import argparse
import csv
import json
from pathlib import Path

from eval.sample import EVAL, read_csv
from eval.sample_v15 import SENT_COLS
from nlp.labeling.lfs_v15 import V15_LABELS
from nlp.sources import ROLE_CUES

ROLES = {r for r, _ in ROLE_CUES} | {"unknown", "none"}
ALLOWED = {k: set(v) for k, v in V15_LABELS.items()} | {
    "bike_lane": {"true", "false"},
    "transit": {"true", "false"},
    "role": ROLES,
    "stance_holder": {"source", "outlet", "none"},
}
FIELDS = {
    "test_v15": list(V15_LABELS),
    "dev_v15": list(V15_LABELS),
    "measure_v15": [*V15_LABELS, "stance_holder"],  # stance_holder: D-87, merged by --fields
    "test_v15_topic": ["bike_lane", "transit"],
    "dev_v15_topic": ["bike_lane", "transit"],
    "test_v15_source": ["speaker", "role"],
    "dev_v15_source": ["speaker", "role"],
}


def clean(field: str, value) -> str:
    v = str(value).strip()
    if field == "speaker":
        return v
    v = v.lower()
    if v not in ALLOWED[field]:
        raise ValueError(f"{field}: invalid label {value!r}")
    return v


def merge(rows: list[dict], labels: list[dict], fields: list[str], annotator: str) -> int:
    key = "article_id" if "article_id" in rows[0] else "sentence_id"
    by_id = {r[key]: r for r in rows}
    for lab in labels:
        r = by_id[lab[key]]
        for f in fields:
            r[f] = clean(f, lab[f])
        r["annotator"] = annotator
    return len(labels)


def _write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", choices=list(FIELDS))
    ap.add_argument("labels")
    ap.add_argument("--second", action="store_true")
    ap.add_argument(
        "--fields", nargs="+", help="merge only these labels (e.g. a stance redo, D-81)"
    )
    args = ap.parse_args()
    labels = [json.loads(x) for x in Path(args.labels).read_text().splitlines() if x.strip()]
    fields = FIELDS[args.name]
    if args.fields:
        assert set(args.fields) <= set(fields), args.fields
        fields = args.fields
    if args.second:
        path = EVAL / f"{args.name}_annotator2.csv"
        rows = read_csv(path) if args.fields and path.exists() else []
        have = {r["sentence_id"] for r in rows}
        src = {r["sentence_id"]: r for r in read_csv(EVAL / f"{args.name}.csv")}
        rows += [
            {k: src[lab["sentence_id"]].get(k, "") for k in SENT_COLS}
            for lab in labels
            if lab["sentence_id"] not in have
        ]
        for r in rows:
            for f in fields:
                r.setdefault(f, "")
        merge(rows, labels, fields, "claude-subagent-2")
        _write(path, rows)
        print(f"annotator 2: {len(rows)} rows")
        return
    path = EVAL / f"{args.name}.csv"
    rows = read_csv(path)
    for r in rows:
        for f in fields:
            r.setdefault(f, "")
    n = merge(rows, labels, fields, "claude-subagent")
    _write(path, rows)
    print(f"merged {n} rows into {path}")


if __name__ == "__main__":
    main()
