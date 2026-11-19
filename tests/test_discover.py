from collect.discover import parse_sitemap, topic_hint, url_date


def test_topic_hint_crash_positive_and_negative():
    assert topic_hint("https://x.ca/2024/05/01/cyclist-struck-by-truck-on-bloor/") == "crash"
    assert topic_hint("https://x.ca/news/123/pedestrian-hit-by-ttc-bus/") == "crash"
    assert topic_hint("https://x.ca/2024/05/01/raptors-win-game-seven/") is None


def test_topic_hint_bike_lane_wins_over_crash_words():
    assert topic_hint("https://x.ca/2024/11/20/bill-212-bike-lane-removal-cyclist/") == "bike_lane"


def test_topic_hint_transit():
    assert topic_hint("https://x.ca/news/1/ttc-fare-freeze-budget/") == "transit"


def test_url_date():
    assert url_date("https://toronto.citynews.ca/2023/03/15/slug/") == "2023-03-15"
    assert url_date("https://globalnews.ca/news/123/slug/") is None


def test_parse_sitemap_with_and_without_lastmod():
    xml = (
        "<url><loc>https://a.ca/1/</loc><lastmod>2024-01-01T00:00Z</lastmod></url>"
        "<url><loc>https://a.ca/2/?a=1&amp;b=2</loc></url>"
    )
    assert parse_sitemap(xml) == [
        ("https://a.ca/1/", "2024-01-01T00:00Z"),
        ("https://a.ca/2/?a=1&b=2", None),
    ]


def test_fetch_tiers():
    from collect.discover import fetch_tier

    assert fetch_tier("https://x.ca/2023/01/02/pedestrian-struck-on-bloor/") == 1
    assert fetch_tier("https://x.ca/2023/01/02/woman-71-struck-by-falling-pole/") == 1
    assert fetch_tier("https://x.ca/2023/01/02/fatal-crash-on-highway-401/") == 2
    assert fetch_tier("https://x.ca/2023/01/02/food-prices-hit-record-high/") is None
