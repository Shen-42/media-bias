from nlp.topic import topics


def test_bike_lane_from_headline_or_lead():
    assert "bike_lane" in topics(
        "Council votes to keep the Bloor bike lanes", "Council voted 20-5."
    )
    lead = (
        "The province will begin removing the bike lanes on Yonge Street."
        "\nThe bike lanes opened in 2021."
    )
    assert "bike_lane" in topics("Work starts next week", lead)


def test_bike_lane_not_from_one_mention_in_crash_story():
    text = (
        "A cyclist was struck by a driver on Monday.\nPolice are investigating."
        "\nThe street has a painted bike lane."
    )
    assert "bike_lane" not in topics("Cyclist struck on Bloor", text)
    # crash headline that names the lane is still a crash story (codebook 7.1)
    assert "bike_lane" not in topics("Cyclist struck in Bloor bike lane", text)


def test_transit_positive_and_negative():
    assert "transit" in topics("TTC fares to rise 10 cents in January", "The board voted Tuesday.")
    lead = "The Eglinton Crosstown opened to riders on Sunday.\nThe LRT runs 19 km across midtown."
    assert "transit" in topics("Opening day", lead)
    assert "transit" not in topics(
        "Pedestrian struck by TTC bus", "A TTC bus hit a man.\nHe was hurt."
    )
    assert "transit" not in topics("Highway 401 lanes closed", "Lanes are closed for paving.")
    assert "transit" not in topics("GO train collides with vehicle", "A GO train hit a car.")
    assert "transit" not in topics("Driver arrested after crashing into TTC bus", "The TTC said.")


def test_one_passing_mention_is_not_a_topic():
    text = "Police launched an e-bike enforcement blitz.\nRiders in bike lanes were stopped."
    assert "bike_lane" not in topics("Police target e-bike riders", text)


def test_bill_212_and_court_stories_are_bike_lane():
    t = "Court of Appeal rules on Reducing Gridlock Act"
    assert "bike_lane" in topics(t, "The ruling concerns lanes on Bloor, Yonge and University.")


def test_incident_on_transit_is_not_transit():
    for title in [
        "Four in custody after stabbing at Don Mills subway",
        "Knifepoint robbery reported at Toronto subway station",
        "Man, 36, charged in unprovoked stabbing of TTC employee",
        "Police seek suspect after man allegedly pushed onto subway tracks",
    ]:
        assert topics(title, "") == [], title
    assert topics("TTC fares to rise 10 cents in January", "") == ["transit"]
    assert topics("TTC adds overnight buses after riders raise safety concerns", "") == ["transit"]


def test_more_incident_headlines_are_not_transit():
    # quality check 2026-11-22 (dev topic sample 2)
    for title in [
        "Man who attacked women on the subway sentenced to life",
        "Bus shelters damaged in overnight mischief spree",
        "Four males threaten TTC employee at Warden Station",
    ]:
        assert topics(title, "") == [], title
    assert topics("TTC board approves new subway cars", "") == ["transit"]
