import pandas as pd

from analysis.aggregate import rate_ci, rates


def test_rate_ci_point_estimate_and_bounds():
    df = pd.DataFrame({"article_id": ["a", "a", "b", "c"], "x": [1.0, 0.0, 1.0, 0.0]})
    est, lo, hi, n, n_art = rate_ci(df, "x")
    assert est == 0.5 and n == 4 and n_art == 3
    assert 0.0 <= lo <= est <= hi <= 1.0


def test_rates_by_group():
    df = pd.DataFrame(
        {"article_id": ["a", "b", "c", "d"], "outlet": ["x", "x", "y", "y"], "m": [1.0, 1.0, 0, 0]}
    )
    out = rates(df, ["outlet"], ["m"]).set_index("outlet")
    assert out.loc["x", "rate"] == 1.0 and out.loc["y", "rate"] == 0.0


def test_common_window_is_intersection():
    from analysis.aggregate import common_window

    arts = pd.DataFrame(
        {
            "outlet": ["a", "a", "b", "b"],
            "published": ["2023-01-05", "2026-10-01", "2025-01-02", "2026-09-30"],
        }
    )
    assert common_window(arts) == ("2025-01-02", "2026-09-30")


def test_pre_post_keeps_only_outlets_on_both_sides():
    from analysis.aggregate import pre_post

    df = pd.DataFrame(
        {"outlet": ["a", "a", "b"], "published": ["2024-06-01", "2025-06-01", "2025-06-01"]}
    )
    out = pre_post(df, "2024-11-25")
    assert set(out["outlet"]) == {"a"}
    assert list(out["period"]) == ["pre", "post"]


def test_coverage_by_quarter():
    from analysis.aggregate import coverage_by_quarter

    arts = pd.DataFrame(
        {
            "article_id": ["1", "2", "3"],
            "outlet": ["a", "a", "b"],
            "published": ["2025-01-05", "2025-02-01", "2025-04-02"],
            "article_type": ["initial", "follow_up", "initial"],
        }
    )
    cov = coverage_by_quarter(arts).set_index("quarter")
    assert cov.loc["2025Q1", "a"] == 2 and cov.loc["2025Q2", "b"] == 1


def test_pooled_shares_flags_largest_outlet():
    from analysis.aggregate import pooled_shares

    df = pd.DataFrame({"article_id": ["1", "1", "2", "3"], "outlet": ["a", "a", "a", "b"]})
    s = pooled_shares({"x": df}).set_index("outlet")
    assert s.loc["a", "units"] == 3 and s.loc["a", "articles"] == 2
    assert s.loc["a", "share_units"] == 0.75 and bool(s.loc["a", "largest"])
    assert not bool(s.loc["b", "largest"])
