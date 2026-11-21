import pytest

from eval.merge_v15 import clean, merge


def test_clean_rejects_values_outside_codebook():
    assert clean("stance_cyclists", "Negative") == "negative"
    assert clean("role", "vru_advocate") == "vru_advocate"
    with pytest.raises(ValueError):
        clean("stance_infrastructure", "positive")


def test_merge_by_article_id():
    rows = [{"article_id": "a1", "bike_lane": "", "transit": "", "annotator": ""}]
    merge(
        rows,
        [{"article_id": "a1", "bike_lane": True, "transit": False}],
        ["bike_lane", "transit"],
        "claude-subagent",
    )
    assert rows[0]["bike_lane"] == "true" and rows[0]["annotator"] == "claude-subagent"
