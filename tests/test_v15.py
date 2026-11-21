from nlp import v15


def row(text, quoted=False, attributed=False):
    return {"text": text, "quoted": quoted, "attributed": attributed, "nli": None, "qwen": None}


def test_labels_for_only_adds_stance_with_target():
    assert v15.labels_for("Work begins Monday.") == ["policy_frame"]
    assert v15.labels_for("Cyclists use the bike lanes on Bloor.") == [
        "policy_frame",
        "stance_infrastructure",
        "stance_cyclists",
    ]
    assert v15.labels_for("The TTC raised fares.")[-1] == "stance_transit"


def test_label_matrix_maps_values_and_abstains():
    m = v15.label_matrix("stance_infrastructure", [row("Buses were late.")])
    vals = v15.lfs_v15.V15_LABELS["stance_infrastructure"]
    assert m.shape == (1, len(v15.lfs_v15.LFS["stance_infrastructure"]))
    assert m[0, 0] == vals.index("none")  # no target
    assert m[0, -1] == -1  # qwen abstains


def test_training_set_caps_and_drops_unconfident():
    vals = ["support", "oppose", "none"]
    texts = [f"s{i}" for i in range(500)] + ["unsure"]
    proba = [[0.0, 0.0, 1.0]] * 450 + [[0.9, 0.05, 0.05]] * 50 + [[0.4, 0.3, 0.3]]
    xs, ys = v15.training_set(texts, proba, vals)
    assert "unsure" not in xs
    assert ys.count(2) == v15.CAP["none"] and ys.count(0) == 50
