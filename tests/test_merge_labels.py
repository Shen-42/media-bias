import pytest

from eval.merge_labels import clean, merge


def test_clean_rejects_non_codebook_labels():
    assert clean("voice", "Active") == "active"
    assert clean("voice", "not_crash") == "not_crash"
    with pytest.raises(ValueError):
        clean("voice", "passive")
    with pytest.raises(ValueError):
        clean("thematic_cue", "not_crash")


def test_merge_sets_annotator_and_requires_full_coverage():
    rows = [{"sentence_id": "a", "set": "context", "vru_conduct_detail": "", "thematic_cue": ""}]
    n = merge(
        rows,
        "context",
        [{"sentence_id": "a", "vru_conduct_detail": "false", "thematic_cue": "true"}],
    )
    assert n == 1 and rows[0]["annotator"] == "claude-subagent"
    rows.append({"sentence_id": "b", "set": "context", "vru_conduct_detail": ""})
    with pytest.raises(ValueError):
        merge(rows, "context", [])
