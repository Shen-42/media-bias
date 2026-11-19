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
