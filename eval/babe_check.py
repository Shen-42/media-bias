"""Component check of the BABE loaded-language score (nlp/v15.step_babe) on BABE's test split.

BABE (Spinde et al. 2021) has expert sentence labels: biased (1) or not (0). The model in
use (`mediabiasgroup/da-roberta-babe-ft`, 2022) predates the Hugging Face train/test split
(2024) and may have been trained on these sentences, so the result is an upper bound (D-96).
The data stay in data/external/babe; only aggregate metrics are written.

    python -m eval.babe_check
"""

from pathlib import Path

import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

from common import config
from nlp.v15 import _biased_label, _score

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "external" / "babe" / "test.parquet"
OUT = ROOT / "eval" / "reports" / "babe_loaded_language.csv"


def metrics(gold: pd.Series, score: pd.Series, threshold: float = 0.5) -> dict:
    pred = (score >= threshold).astype(int)
    return {
        "n": len(gold),
        "biased_share_gold": float(gold.mean()),
        "biased_share_pred": float(pred.mean()),
        "accuracy": float((pred == gold).mean()),
        "macro_f1": float(f1_score(gold, pred, average="macro")),
        "auc": float(roc_auc_score(gold, score)),
    }


def main() -> None:
    from transformers import pipeline

    from nlp.device import get_device

    d = pd.read_parquet(DATA)
    m = config.load()["models"]["babe"]
    clf = pipeline(
        "text-classification", model=m["name"], revision=m["revision"], device=get_device()
    )
    biased = _biased_label(clf.model.config.id2label)
    outs = clf(d.text.tolist(), top_k=None, truncation=True, batch_size=32)
    d["score"] = [_score(o, biased) for o in outs]
    res = metrics(d.label, d.score)
    by = [{"group": "all", **res}]
    for lean, sub in d.groupby("type"):
        by.append({"group": f"outlet_lean_{lean}", **metrics(sub.label, sub.score)})
    out = pd.DataFrame(by)
    out.to_csv(OUT, index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
