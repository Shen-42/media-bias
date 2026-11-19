from collect.police import is_collision, parse_release

HTML = """<html><head><title>Fatal Collision,
Pedestrian Struck,
Bloor Street West and Spadina Avenue area</title></head><body>
<nav>Menu</nav>
<p>Published: Tuesday, March 14, 2023, 9:10 AM</p><p>Share (opens in new window)</p>
<p>The Toronto Police Service is investigating a fatal collision.</p>
<p>It is reported that a vehicle was travelling eastbound and struck a pedestrian.</p>
<p>For more news, visit TPSnews.ca.</p></body></html>"""


def test_parse_release_extracts_title_date_and_body():
    rec = parse_release(HTML)
    assert rec["title"].startswith("Fatal Collision, Pedestrian Struck")
    assert rec["published"] == "2023-03-14"
    assert "struck a pedestrian" in rec["text"]
    assert "For more news" not in rec["text"]
    assert "Menu" not in rec["text"]


def test_is_collision_positive_and_negative():
    assert is_collision("Fatal Collision, Pedestrian Struck", "")
    assert not is_collision("Man Arrested in Robbery Investigation", "A man was arrested.")
