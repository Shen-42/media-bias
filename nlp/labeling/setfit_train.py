"""SetFit end model (all-MiniLM-L6-v2) trained on Snorkel labels (PLAN.md §8.1, D-35)."""

import random

from common import config

POS_T, NEG_T = 0.7, 0.3
MAX_PER_CLASS = 200


def training_set(texts: list[str], proba, seed: int = 0) -> tuple[list[str], list[int]]:
    """Confident Snorkel labels only, capped and class-balanced up to MAX_PER_CLASS."""
    pos = [t for t, p in zip(texts, proba, strict=True) if p >= POS_T]
    neg = [t for t, p in zip(texts, proba, strict=True) if p <= NEG_T]
    rng = random.Random(seed)
    rng.shuffle(pos)
    rng.shuffle(neg)
    n = min(MAX_PER_CLASS, len(pos))
    pos, neg = pos[:n], neg[: max(n, min(MAX_PER_CLASS, len(neg)))]
    return pos + neg, [1] * len(pos) + [0] * len(neg)


def train(texts: list[str], labels: list[int]):
    from datasets import Dataset
    from setfit import SetFitModel, Trainer, TrainingArguments

    m = config.load()["models"]["setfit_base"]
    model = SetFitModel.from_pretrained(m["name"], revision=m["revision"])
    args = TrainingArguments(num_epochs=1, batch_size=16, num_iterations=10, seed=0)
    ds = Dataset.from_dict({"text": texts, "label": labels})
    Trainer(model=model, args=args, train_dataset=ds).train()
    return model


def predict(model, texts: list[str]) -> list[float]:
    probs = model.predict_proba(texts, batch_size=64)
    return [float(p[1]) for p in probs]
