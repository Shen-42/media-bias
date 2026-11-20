from collect.crash import (
    article_type,
    assign_crash_ids,
    is_crash_article,
    is_toronto,
    link_release,
    road_users,
    severity,
    streets,
)


def test_is_toronto():
    assert is_toronto("Cyclist hit on Bloor", "Toronto police say a cyclist was struck.")
    assert not is_toronto(
        "Pedestrian hit", "Peel Regional Police say a man was struck in Brampton."
    )
    assert not is_toronto("Pedestrian hit in Mississauga", "A man was struck near Toronto.")


def test_severity():
    assert severity("Cyclist killed on Bloor", "") == "fatal"
    assert severity("Pedestrian injured", "taken to hospital") == "injury"
    assert severity("Crash on Queen", "No one was hurt.") == "no_injury"
    assert severity("Crash on Queen", "Police are investigating.") == "unknown"


def test_streets_and_intersections():
    s = streets("A cyclist was struck near Bloor Street West and Spadina Avenue.")
    assert {"bloor", "spadina"} <= s
    assert "yonge" in streets("It happened at Yonge and Eglinton on Monday.")


def test_road_users():
    assert road_users("A cyclist was hit by a streetcar.", "The driver stayed.") == [
        "cyclist",
        "driver",
        "transit_vehicle",
    ]


def test_is_crash_article():
    assert is_crash_article(["A cyclist was struck by a car."], "Cyclist hit", "A car hit…")
    assert not is_crash_article(["Two cars collided on the 401."], "Crash on 401", "Two cars.")
    assert not is_crash_article([], "Cyclist hit", "")


def test_article_type():
    assert article_type("Driver charged in crash that killed cyclist", "") == "follow_up"
    assert article_type("Three pedestrians struck in separate collisions", "") == "roundup"
    assert article_type("Cyclist struck on Bloor", "") == "initial"


def test_link_release_needs_shared_streets():
    art = {
        "published": "2024-05-02",
        "streets": {"bloor", "spadina"},
        "road_users": ["cyclist"],
        "article_type": "initial",
    }
    rel_ok = {
        "id": 1,
        "published": "2024-05-01",
        "streets": {"bloor", "spadina"},
        "road_users": ["cyclist"],
    }
    rel_bad = {"id": 2, "published": "2024-05-01", "streets": {"finch"}, "road_users": ["cyclist"]}
    assert link_release(art, [rel_bad, rel_ok])[0] == 1
    assert link_release(art, [rel_bad])[0] is None


def test_assign_crash_ids_groups_and_marks_follow_up():
    base = {"streets": {"bloor", "spadina"}, "road_users": ["cyclist"], "release_id": None}
    arts = [
        {**base, "id": "a", "outlet": "ctv", "published": "2024-05-01", "article_type": "initial"},
        {**base, "id": "b", "outlet": "ctv", "published": "2024-05-02", "article_type": "initial"},
        {
            **base,
            "id": "c",
            "outlet": "global",
            "published": "2024-05-01",
            "article_type": "initial",
        },
        {
            **base,
            "id": "d",
            "outlet": "ctv",
            "published": "2024-05-01",
            "article_type": "initial",
            "streets": {"finch", "keele"},
        },
    ]
    assign_crash_ids(arts)
    by = {a["id"]: a for a in arts}
    assert by["a"]["crash_id"] == by["b"]["crash_id"] == by["c"]["crash_id"]
    assert by["d"]["crash_id"] != by["a"]["crash_id"]
    assert by["b"]["article_type"] == "follow_up"
    assert by["c"]["article_type"] == "initial"


def test_is_toronto_local_outlet_default():
    text = "A pedestrian was struck at Eglinton and Miranda Avenue."
    assert is_toronto("Pedestrian struck", text, local=True)
    assert not is_toronto("Pedestrian struck", text, local=False)
    assert not is_toronto("Pedestrian struck in Vaughan", text, local=True)


def test_person_struck_counts_as_pedestrian():
    sents = ["A woman in her 70s was hit by a streetcar."]
    assert is_crash_article(sents, "Woman struck by streetcar", "streetcar")
    assert "pedestrian" in road_users(sents[0], "")
    assert not is_crash_article(
        ["The driver of a car and his passenger were hit by a truck."], "Crash", "truck"
    )


def test_local_outlet_wire_story_elsewhere_is_not_toronto():
    # D-54: Toronto-section pages carry wire copy; a place elsewhere in the lead or a wire
    # credit with no Toronto signal anywhere means the story is not local.
    us = "PHOENIX (AP) — A pickup struck a group of bicyclists in Arizona, killing two."
    assert not is_toronto("2 killed after pickup strikes bicyclists", us, local=True)
    bc = "A stroller was hit and dragged by a vehicle in Squamish, B.C., on Monday."
    assert not is_toronto("Baby lives after stroller hit", bc, local=True)
    ont = "A pedestrian died after a crash in East Gwillimbury, Ont., police say."
    assert not is_toronto("One dead in East Gwillimbury", ont, local=True)
    wire = "A man was struck by a car on Tuesday. — The Associated Press"
    assert not is_toronto("Man struck", wire, local=True)


def test_local_outlet_toronto_signal_wins_over_elsewhere():
    text = "A cyclist from Quebec was struck in Scarborough on Monday, police said."
    assert is_toronto("Cyclist struck", text, local=True)
    assert is_toronto("Woman struck in Leslieville", "A woman was hit by a driver.", local=True)


def test_bare_person_needs_to_be_struck():
    # D-54: the D-39 fallback needs the person to be the one hit, not a car occupant
    # mentioned near a collision noun.
    car_only = ["A man was critically injured in a three-vehicle crash in Rexdale."]
    assert not is_crash_article(car_only, "Man injured in 3-vehicle crash", "vehicle")
    struck = ["A girl, 14, was struck by a truck in Rexdale."]
    assert is_crash_article(struck, "Girl struck by truck", "truck")
    after = ["A 14-year-old boy suffered life-threatening injuries after he was hit by a car."]
    assert is_crash_article(after, "Boy hit by car", "car")
    pole = ["A man was injured after a car hit a pole in Scarborough."]
    assert not is_crash_article(pole, "Man injured in crash", "car")
    headline = ["Man, 62, struck by TTC streetcar downtown dies in hospital"]
    assert is_crash_article(headline, "Man struck", "streetcar")
    active = ["Police say man struck vehicle with hatchet while yelling at driver"]
    assert not is_crash_article(active, "Man struck vehicle", "vehicle")
    ran_over = ["The driver ran over a woman in the parking lot."]
    assert is_crash_article(ran_over, "Woman run over", "driver")
