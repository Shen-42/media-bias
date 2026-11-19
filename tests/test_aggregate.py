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
