import pandas as pd
import pytest

from analysis.measure_v15 import stratified_rate


def test_stratified_rate_weights_outlets_not_rows():
    # outlet a: 1/1 stance; outlet b: 0/3. Unweighted row mean 0.25; equal weights give 0.5.
    df = pd.DataFrame(
        {
            "outlet": ["a", "b", "b", "b"],
            "article_id": ["a1", "b1", "b2", "b3"],
            "v": [1.0, 0.0, 0.0, 0.0],
        }
    )
    est, lo, hi, n = stratified_rate(df, "v", {"a": 0.5, "b": 0.5})
    assert est == pytest.approx(0.5) and n == 4
    assert lo <= est <= hi
    est, *_ = stratified_rate(df, "v", {"a": 0.1, "b": 0.9})
    assert est == pytest.approx(0.1)


def test_stratified_rate_skips_missing():
    df = pd.DataFrame({"outlet": ["a", "a"], "article_id": ["x", "y"], "v": [1.0, None]})
    assert stratified_rate(df, "v", {"a": 1.0})[3] == 1
