from eval import score_v15


def test_score_uses_headline_sample_and_counts_abstain():
    gold = [
        {
            "sentence_id": "a",
            "sample": "random",
            "policy_frame": "economic",
            "stance_infrastructure": "none",
            "stance_cyclists": "none",
            "stance_transit": "none",
        },
        {
            "sentence_id": "b",
            "sample": "random",
            "policy_frame": "none",
            "stance_infrastructure": "none",
            "stance_cyclists": "none",
            "stance_transit": "none",
        },
    ]
    preds = {}
    for g in gold:
        for label in score_v15.v15.LABELS:
            for s in score_v15.SYSTEMS:
                preds[(g["sentence_id"], label, s)] = g[label]
    preds[("b", "policy_frame", "nli")] = "abstain"
    summary, _ = score_v15.score(gold, preds)
    row = summary[(summary.label == "policy_frame") & (summary.system == "nli")].iloc[0]
    assert row.headline and row.coverage == 0.5 and row.accuracy == 0.5
    stance = summary[summary.label == "stance_transit"]
    assert not stance.headline.any()  # stance headline rows are random_target only
