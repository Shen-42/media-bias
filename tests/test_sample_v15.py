import random

from eval import sample_v15


def test_draw_skips_taken_and_excluded_ids():
    items = [{"id": f"s{i}"} for i in range(10)]
    taken = {"s0", "s1", "s2"}
    out = sample_v15.draw(items, 3, taken, random.Random(0))
    assert [x["id"] for x in out] == ["s3", "s4", "s5"]
    assert {"s3", "s4", "s5"} <= taken


def test_has_target():
    assert sample_v15.has_target("The bike lanes on Bloor stay.")
    assert not sample_v15.has_target("Council met on Tuesday.")


def test_committed_columns_exclude_text():
    for cols in (sample_v15.SENT_COLS, sample_v15.TOPIC_COLS, sample_v15.SOURCE_COLS):
        assert "text" not in cols and "sentence" not in cols
