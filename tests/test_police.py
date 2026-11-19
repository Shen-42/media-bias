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


def test_failed_ids_reads_only_non_ok(tmp_path):
    from collect.police import failed_ids
    from common import db

    con = db.connect(str(tmp_path / "t.sqlite"))
    con.execute("INSERT INTO police_releases VALUES (1,'u1','t1',NULL,NULL,'',0,'ok')")
    con.execute("INSERT INTO police_releases VALUES (2,'u2','t2',NULL,NULL,'',0,'http_404')")
    assert failed_ids(con) == {2: ("t2", "u2")}
