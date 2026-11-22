import pandas as pd

from analysis.ksi_link import collisions, coverage, link, matches, street_pattern


def test_street_pattern_drops_suffix_and_direction():
    p = street_pattern("LAKE SHORE BLVD W")
    assert p.search("on Lakeshore Boulevard West") and p.search("Lake Shore Blvd.")
    assert not street_pattern("QUEEN ST E").search("the Queensway")
    assert street_pattern(None) is None and street_pattern("ST") is None


def _row(st1, st2=None, st3=None):
    return pd.Series({"st1": st1, "st2": st2, "st3": st3})


def test_match_needs_main_and_cross_street():
    text = "A cyclist was hit near Bathurst Street and Haddington Avenue."
    assert matches(text, _row("BATHURST ST", "HADDINGTON AVE"))
    assert not matches(text, _row("BATHURST ST", "EGLINTON AVE W"))
    assert matches(text, _row("BATHURST ST"))


def _ksi():
    return pd.DataFrame(
        {
            "collision_id": ["c1", "c1", "c2", "c3"],
            "accdate": [
                "2024-05-01 10:00",
                "2024-05-01 10:00",
                "2024-05-02 08:00",
                "2024-05-03 09:00",
            ],
            "stname1": ["BATHURST ST", "BATHURST ST", "KEELE ST", "JANE ST"],
            "stname2": ["HADDINGTON AVE"] * 2 + [None, None],
            "stname3": [None] * 4,
            "road_user": ["driver", "pedestrian", "driver", "driver"],
            "pedestrian": [True, True, False, False],
            "cyclist": [False, False, True, False],
            "injury": ["None", "Fatal", "Major", "Major"],
            "acclass": ["Fatal Injury", "Fatal Injury", "Non-Fatal Injury", "Non-Fatal Injury"],
        }
    )


def test_collisions_keep_vru_crashes_only():
    c = collisions(_ksi())
    assert set(c.collision_id) == {"c1", "c2"}
    assert c.set_index("collision_id").fatal.to_dict() == {"c1": True, "c2": False}


def test_link_respects_publication_lag_and_coverage_counts():
    cols = collisions(_ksi())
    arts = pd.DataFrame(
        {
            "id": ["a1", "a2"],
            "text": ["Hit at Bathurst St. and Haddington Ave.", "Cyclist hurt on Keele Street."],
            "date": pd.to_datetime(["2024-05-02", "2024-05-06"]),
        }
    )
    linked = link(arts, cols)
    assert linked.to_dict("records") == [{"article_id": "a1", "collision_id": "c1"}]
    cov = coverage(cols, linked).set_index(["group", "value"])
    assert cov.loc[("all", "all"), "covered"] == 1 and cov.loc[("all", "all"), "n"] == 2
