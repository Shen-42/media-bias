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


def test_measure_rows_census_and_transit_draw(monkeypatch):
    monkeypatch.setattr(sample_v15, "MEASURE_TRANSIT", 1)
    sents = [
        {"id": "a", "part": "body", "outlet": "x", "text": "The bike lanes on Bloor stay."},
        {"id": "h", "part": "headline", "outlet": "x", "text": "Bike lanes stay"},
        {"id": "t1", "part": "body", "outlet": "x", "text": "The TTC raised fares."},
        {"id": "t2", "part": "body", "outlet": "x", "text": "The TTC cut service."},
        {"id": "t3", "part": "body", "outlet": "y", "text": "The TTC added buses."},
        {"id": "n", "part": "body", "outlet": "y", "text": "Council met on Tuesday."},
    ]
    out = {s["id"]: tag for s, tag in sample_v15.measure_rows(sents, random.Random(0))}
    assert out["a"] == "census"
    assert "h" not in out and "n" not in out  # headlines and no-target sentences are skipped
    assert out["t3"] == "transit_random"  # one per outlet
    assert sum(k in out for k in ("t1", "t2")) == 1
