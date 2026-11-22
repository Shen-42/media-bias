"""Component check of the `attributed` rule (nlp/quotes.is_attributed, D-91) on PolNeAR.

PolNeAR (Newell et al. 2018) annotates attribution relations in 2016 US election news. A
sentence counts as gold-attributed if it holds an attribution cue span. Only sentences that
the pipeline would not mark `quoted` (most of the sentence inside quotation marks) are scored,
as in the pipeline's precedence. The corpus has no licence, so it stays in data/ (D-94) and
only aggregate metrics are written. Uses the `test` compartment; nothing is tuned on it.

    python -m eval.polnear_check --root data/external/polnear/data/test
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from eval.validate_endmodel import wilson
from nlp.quotes import is_attributed, is_quoted, quote_spans

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval" / "reports" / "polnear_attribution.csv"


def cue_spans(ann: str) -> list[tuple[int, int]]:
    """Character spans of every Cue in a brat .ann file (discontinuous spans split)."""
    spans = []
    for line in ann.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0].startswith("T"):
            continue
        kind, _, offsets = parts[1].partition(" ")
        if kind != "Cue":
            continue
        for piece in offsets.split(";"):
            a, b = piece.split()
            spans.append((int(a), int(b)))
    return spans


def sentence_spans(corenlp_xml: str) -> list[tuple[int, int]]:
    root = ET.fromstring(corenlp_xml)
    out = []
    for sent in root.iter("sentence"):
        b = [int(t.text) for t in sent.iter("CharacterOffsetBegin")]
        e = [int(t.text) for t in sent.iter("CharacterOffsetEnd")]
        if b:
            out.append((min(b), max(e)))
    return out


def label_sentences(text: str, sents, cues) -> list[dict]:
    qs = quote_spans(text)
    rows = []
    for a, b in sents:
        if is_quoted(a, b, qs):
            continue
        rows.append(
            {
                "gold": any(ca < b and cb > a for ca, cb in cues),
                "pred": is_attributed(text[a:b]),
            }
        )
    return rows


def metrics(df: pd.DataFrame) -> dict:
    tp = int((df.gold & df.pred).sum())
    npred, ngold = int(df.pred.sum()), int(df.gold.sum())
    p_lo, p_hi = wilson(tp, npred)
    r_lo, r_hi = wilson(tp, ngold)
    return {
        "n_sentences": len(df),
        "gold_attributed": ngold,
        "pred_attributed": npred,
        "precision": tp / npred if npred else float("nan"),
        "precision_lo": p_lo,
        "precision_hi": p_hi,
        "recall": tp / ngold if ngold else float("nan"),
        "recall_lo": r_lo,
        "recall_hi": r_hi,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT / "data/external/polnear/data/test")
    args = ap.parse_args()
    rows = []
    for tf in sorted((args.root / "text").glob("*.txt")):
        # .ann files carry an annotator suffix; the first annotator's file is used
        anns = sorted((args.root / "attributions").glob(tf.stem + "_*.ann"))
        xml = args.root / "corenlp" / (tf.name + ".xml")
        if not (anns and xml.exists()):
            continue
        ann = anns[0]
        text = tf.read_text(encoding="utf-8")
        rows += label_sentences(text, sentence_spans(xml.read_text()), cue_spans(ann.read_text()))
    m = metrics(pd.DataFrame(rows))
    m["articles"] = len(list((args.root / "text").glob("*.txt")))
    pd.DataFrame([m]).to_csv(OUT, index=False)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()})


if __name__ == "__main__":
    main()
