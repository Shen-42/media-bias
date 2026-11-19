"""Component check: passive detection (nlp.rules.is_passive) on UD English EWT test.

Gold: a participle (xpos VBN) is passive if it carries Voice=Pass or has an aux:pass /
nsubj:pass / csubj:pass dependent. Reported separately from end-to-end metrics (CLAUDE.md).
Data: UD_English-EWT (CC BY-SA 4.0), downloaded to data/ud/ (not committed).
"""

import argparse
from pathlib import Path

import pandas as pd
import spacy

from common import config
from nlp.rules import is_passive

PASSIVE_DEPS = {"aux:pass", "nsubj:pass", "csubj:pass"}


def read_conllu(path: Path):
    sent, text = [], None
    for line in path.read_text().splitlines():
        if line.startswith("# text = "):
            text = line[9:]
        elif not line.strip():
            if sent:
                yield text, sent
            sent, text = [], None
        elif not line.startswith("#"):
            cols = line.split("\t")
            if "-" in cols[0] or "." in cols[0]:
                continue
            sent.append(cols)
    if sent:
        yield text, sent


def gold_passive_offsets(text: str, toks: list[list[str]]) -> dict[int, bool]:
    """Char offset of each VBN token -> gold passive."""
    heads_with = {}
    for c in toks:
        if c[7] in PASSIVE_DEPS:
            heads_with[c[6]] = True
    out, pos = {}, 0
    for c in toks:
        i = text.find(c[1], pos)
        if i < 0:
            continue
        pos = i + len(c[1])
        if c[4] == "VBN":
            out[i] = "Voice=Pass" in c[5] or heads_with.get(c[0], False)
    return out


def objects(t) -> bool:
    return any(c.dep_ in ("dobj", "obj", "dative") for c in t.children)


def run(path: Path, model: str) -> pd.DataFrame:
    nlp = spacy.load(model)
    data = list(read_conllu(path))
    rows = []
    for (text, toks), doc in zip(data, nlp.pipe([t for t, _ in data], batch_size=32), strict=True):
        gold = gold_passive_offsets(text, toks)
        for t in doc:
            if t.idx in gold:
                rows.append(
                    {
                        "gold": gold[t.idx],
                        "pred": is_passive(t, objects(t)),
                        "attributive": t.dep_ in ("amod", "compound"),
                    }
                )
    return pd.DataFrame(rows)


def metrics(df: pd.DataFrame) -> dict:
    tp = int((df.gold & df.pred).sum())
    fp = int((~df.gold & df.pred).sum())
    fn = int((df.gold & ~df.pred).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {
        "n_participles": len(df),
        "gold_passive": int(df.gold.sum()),
        "precision": p,
        "recall": r,
        "f1": f,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conllu", default=str(config.ROOT / "data" / "ud" / "en_ewt-ud-test.conllu"))
    ap.add_argument("--model", default="en_core_web_trf")
    args = ap.parse_args()
    df = run(Path(args.conllu), args.model)
    # Prenominal participles ("a revised offer") never head an impact clause; report both.
    ms = [
        {"model": args.model, "subset": "all_participles", **metrics(df)},
        {
            "model": args.model,
            "subset": "clausal_participles",
            **metrics(df[~df.attributive].reset_index(drop=True)),
        },
    ]
    out = config.ROOT / "eval" / "reports" / "component_ud_passive.csv"
    out.parent.mkdir(exist_ok=True)
    pd.DataFrame(ms).to_csv(out, index=False)
    print(pd.DataFrame(ms).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
