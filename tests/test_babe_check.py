import pandas as pd

from eval.babe_check import metrics


def test_metrics_threshold_and_scores():
    gold = pd.Series([1, 1, 0, 0])
    score = pd.Series([0.9, 0.4, 0.2, 0.6])
    m = metrics(gold, score)
    assert m["accuracy"] == 0.5 and m["biased_share_pred"] == 0.5
    assert m["auc"] == 0.75
