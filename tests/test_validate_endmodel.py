import pandas as pd
import pytest

from eval.validate_endmodel import check, wilson


def test_wilson_known_value():
    lo, hi = wilson(0, 20)
    assert lo == 0.0 and hi == pytest.approx(0.161, abs=0.001)


def test_check_flags_rate_outside_interval():
    df = pd.DataFrame(
        {
            "outlet": ["a"] * 50,
            "text_source": ["quoted"] * 50,
            "gold": [1.0] * 5 + [0.0] * 45,
            "pred": [1.0] * 40 + [0.0] * 10,
        }
    )
    res = check(df)
    assert not res.inside.any()
    df["pred"] = df["gold"]
    assert check(df).inside.all()
