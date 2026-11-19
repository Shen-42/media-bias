from eval.score import kappa, macro_f1, norm, score
from eval.tune import best_thresholds


def test_norm():
    assert norm("Yes") == "true" and norm("0") == "false" and norm("") is None


def test_score_uses_random_rows_for_headline_and_counts_abstain_as_wrong():
    gold = [
        {"sentence_id": "s1", "set": "crash", "sample": "random", "voice": "active"},
        {"sentence_id": "s2", "set": "crash", "sample": "random", "voice": "nominal"},
        {"sentence_id": "s3", "set": "crash", "sample": "disagreement", "voice": "active"},
    ]
    for g in gold:
        for k in (
            "driver_reference",
            "focus",
            "vru_as_actor",
            "accident_term",
            "vru_conduct_detail",
            "thematic_cue",
        ):
            g.setdefault(k, "")
    preds = {("s1", "voice", "rule"): "active", ("s3", "voice", "rule"): "nominal"}
    summary, _ = score(gold, preds)
    rule = summary.query("label == 'voice' and system == 'rule'").set_index("sample")
    assert rule.loc["random", "n"] == 2
    assert rule.loc["random", "accuracy"] == 0.5  # s2 abstained
    assert rule.loc["random", "coverage"] == 0.5
    assert rule.loc["disagreement", "accuracy"] == 0.0


def test_macro_f1_perfect():
    assert macro_f1(["a", "b"], ["a", "b"]) == 1.0


def test_kappa_perfect_agreement():
    g = [{"sentence_id": "s1", "voice": "active"}, {"sentence_id": "s2", "voice": "nominal"}]
    for row in g:
        for k in (
            "driver_reference",
            "focus",
            "vru_as_actor",
            "accident_term",
            "vru_conduct_detail",
            "thematic_cue",
        ):
            row[k] = ""
    k = kappa(g, g).set_index("label")
    assert k.loc["voice", "cohen_kappa"] == 1.0


def test_tuning_picks_separating_threshold():
    rows = [
        ("police_matched", False, 0.95, 0.6),
        ("police_matched", False, 0.9, 0.5),
        ("newsroom", False, 0.7, 0.1),
        ("newsroom", False, 0.5, 0.05),
        ("quoted", True, 0.9, 0.6),
    ]
    f, e, c = best_thresholds(rows)
    assert f == 1.0
    assert 0.7 < e <= 0.9 or c > 0.1


def test_not_crash_gold_is_excluded():
    assert norm("not_crash") is None
