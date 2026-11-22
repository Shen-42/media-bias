import pandas as pd

from eval.sample_fr import SIZES, draw
from eval.score_fr import score


def test_draw_splits_do_not_overlap():
    rows = [{"id": f"s{i}", "text": "x", "part": "body"} for i in range(200)]
    s = draw(rows)
    assert len(s["dev"]) == SIZES["dev"] and len(s["test"]) == SIZES["test"]
    assert not {r["id"] for r in s["dev"]} & {r["id"] for r in s["test"]}


def test_score_crash_detection_and_labels():
    base = {"driver_reference": "absent", "focus": "vru", "vru_as_actor": "false",
            "accident_term": "false"}  # fmt: skip
    gold = pd.DataFrame([
        {"sentence_id": "a", "voice": "agentless_passive", **base},
        {"sentence_id": "b", "voice": "active", **base},
        {"sentence_id": "c", "voice": "not_crash", **base},
    ])  # fmt: skip
    pred = pd.DataFrame([
        {"sentence_id": "a", "is_crash": True, "voice": "agentless_passive", **base},
        {"sentence_id": "b", "is_crash": False},
        {"sentence_id": "c", "is_crash": True, "voice": "nominal", **base},
    ])  # fmt: skip
    out = score(gold, pred).set_index("label")
    assert out.loc["crash_precision", "value"] == 0.5
    assert out.loc["crash_recall", "value"] == 0.5
    assert out.loc["voice", "value"] == 1.0 and out.loc["voice", "n"] == 1
