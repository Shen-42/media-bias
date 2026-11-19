"""Snorkel label model over the labeling functions, for the two fuzzy labels only (PLAN.md §9)."""

import numpy as np
import pandas as pd

from nlp.labeling.lfs import ABSTAIN, LFS

SEED = 0


def label_matrix(label: str, rows: list[dict]) -> np.ndarray:
    return np.array([[lf(r) for lf in LFS[label]] for r in rows], dtype=int)


def lf_summary(label: str, L: np.ndarray) -> pd.DataFrame:
    """Coverage, overlap and conflict per LF (agreement statistics, not accuracy)."""
    out = []
    for j, lf in enumerate(LFS[label]):
        col = L[:, j]
        voted = col != ABSTAIN
        others = np.delete(L, j, axis=1)
        other_voted = (others != ABSTAIN).any(axis=1)
        conflict = voted & np.array(
            [any(o != ABSTAIN and o != c for o in row) for c, row in zip(col, others, strict=True)]
        )
        out.append(
            {
                "lf": lf.__name__,
                "coverage": voted.mean(),
                "overlap": (voted & other_voted).mean(),
                "conflict": conflict.mean(),
                "yes_rate": (col == 1).sum() / max(voted.sum(), 1),
            }
        )
    return pd.DataFrame(out)


def fit(label: str, rows: list[dict]):
    """Fit the label model on training rows only. Returns (model, LF summary)."""
    from snorkel.labeling.model import LabelModel

    L = label_matrix(label, rows)
    lm = LabelModel(cardinality=2, verbose=False)
    lm.fit(L, n_epochs=500, seed=SEED, log_freq=1000)
    return lm, lf_summary(label, L)


def predict(lm, label: str, rows: list[dict]) -> np.ndarray:
    """P(label = true). Rows where every LF abstains get the class prior."""
    return lm.predict_proba(label_matrix(label, rows))[:, 1]


def fit_predict(label: str, rows: list[dict]) -> tuple[np.ndarray, pd.DataFrame]:
    lm, summary = fit(label, rows)
    return predict(lm, label, rows), summary
