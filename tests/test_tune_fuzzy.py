from eval.tune_fuzzy import best_cutoff
from nlp.labeling import lfs, setfit_train


def test_best_cutoff_separates_classes():
    gold = [True, True, False, False, False]
    scores = [0.9, 0.7, 0.6, 0.2, 0.1]
    assert best_cutoff(gold, scores, [0.5, 0.65, 0.8]) == 0.65


def test_best_cutoff_prefers_stricter_on_tie():
    gold = [True, False]
    scores = [0.9, 0.1]
    assert best_cutoff(gold, scores, [0.3, 0.5, 0.8]) == 0.8


def test_nli_lf_uses_per_label_cutoff():
    x = {"text": "t", "nli": 0.75, "qwen": None}
    assert lfs._nli(x, hi=0.7) == lfs.YES
    assert lfs._nli(x, hi=0.9) == lfs.ABSTAIN


def test_training_set_keeps_negatives_up_to_ratio():
    texts = [f"p{i}" for i in range(10)] + [f"n{i}" for i in range(100)]
    proba = [0.9] * 10 + [0.1] * 100
    _, y = setfit_train.training_set(texts, proba)
    assert y.count(1) == 10 and y.count(0) == 10 * setfit_train.NEG_RATIO
