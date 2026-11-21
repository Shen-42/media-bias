"""SetFit end model (all-MiniLM-L6-v2) trained on Snorkel labels (PLAN.md §8.1, D-35)."""

import random

from common import config

POS_T, NEG_T = 0.7, 0.3
MAX_PER_CLASS = 200
NEG_RATIO = 3  # D-71: up to 3 negatives per positive; 1:1 made SetFit over-predict rare labels


def training_set(texts: list[str], proba, seed: int = 0) -> tuple[list[str], list[int]]:
    """Confident Snorkel labels only; up to MAX_PER_CLASS positives, NEG_RATIO negatives each."""
    pos = [t for t, p in zip(texts, proba, strict=True) if p >= POS_T]
    neg = [t for t, p in zip(texts, proba, strict=True) if p <= NEG_T]
    rng = random.Random(seed)
    rng.shuffle(pos)
    rng.shuffle(neg)
    n = min(MAX_PER_CLASS, len(pos))
    pos, neg = pos[:n], neg[: max(n, 1) * NEG_RATIO]
    return pos + neg, [1] * len(pos) + [0] * len(neg)


def train(texts: list[str], labels: list[int]):
    from datasets import Dataset
    from huggingface_hub import snapshot_download
    from setfit import SetFitModel, Trainer, TrainingArguments

    m = config.load()["models"]["setfit_base"]
    # Load the pinned snapshot by path: SetFit drops `revision` for inner loads, which
    # fails in offline mode (D-59).
    path = snapshot_download(m["name"], revision=m["revision"], local_files_only=True)
    model = SetFitModel.from_pretrained(path)
    args = TrainingArguments(num_epochs=1, batch_size=16, num_iterations=10, seed=0)
    ds = Dataset.from_dict({"text": texts, "label": labels})
    Trainer(model=model, args=args, train_dataset=ds).train()
    return model


def predict(model, texts: list[str]) -> list[float]:
    probs = model.predict_proba(texts, batch_size=64)
    return [float(p[1]) for p in probs]
