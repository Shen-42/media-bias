import numpy as np

from nlp.labeling.setfit_train import training_set
from nlp.labeling.snorkel_model import fit_predict, label_matrix, lf_summary


def _rows():
    pos = {"text": "The cyclist was not wearing a helmet.", "nli": 0.9, "qwen": "true"}
    neg = {"text": "The cyclist was taken to hospital.", "nli": 0.1, "qwen": "false"}
    return [pos] * 30 + [neg] * 30


def test_label_matrix_shape_and_summary():
    L = label_matrix("vru_conduct_detail", _rows())
    assert L.shape == (60, 5)
    s = lf_summary("vru_conduct_detail", L)
    assert set(s["lf"]) >= {"lf_conduct_lexicon", "lf_conduct_qwen"}
    assert (s["coverage"] >= 0).all()


def test_label_model_separates_clear_cases():
    proba, _ = fit_predict("vru_conduct_detail", _rows())
    assert proba[:30].mean() > 0.7
    assert proba[30:].mean() < 0.3


def test_training_set_uses_confident_rows_only():
    texts = ["a", "b", "c", "d"]
    t, y = training_set(texts, np.array([0.9, 0.5, 0.1, 0.8]))
    assert sorted(zip(t, y, strict=True)) == [("a", 1), ("c", 0), ("d", 1)]
