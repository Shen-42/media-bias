from collect.fetch import fetch_order


def test_crash_topic_uses_slug_tiers():
    urls = [
        "https://x.ca/2024/01/02/three-vehicle-crash-on-401",
        "https://x.ca/2024/01/01/cyclist-struck-on-bloor",
        "https://x.ca/2024/01/03/prices-hit-record-high",
    ]
    keep, noise = fetch_order(urls, "crash")
    assert keep[0].endswith("cyclist-struck-on-bloor")
    assert "https://x.ca/2024/01/03/prices-hit-record-high" in noise


def test_other_topics_skip_crash_tiers():
    # The crash slug tiers would mark every bike lane or transit URL as noise.
    urls = [
        "https://x.ca/2025/01/01/bloor-bike-lanes-removal",
        "https://x.ca/2025/01/02/ttc-budget",
    ]
    keep, noise = fetch_order(urls, "bike_lane")
    assert keep == urls
    assert noise == []
