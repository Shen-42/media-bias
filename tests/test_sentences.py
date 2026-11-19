from nlp.sentences import CANDIDATE_RE, clean_body


def test_clean_body_drops_repeated_headline_and_dateline():
    title = "Pedestrian struck on Bloor"
    text = "Pedestrian struck on Bloor\nPosted January 2, 2023 10:55 pm.\nA pedestrian was hit."
    assert clean_body(title, text) == "A pedestrian was hit."


def test_clean_body_keeps_normal_sentences():
    assert clean_body("T", "Police said the driver stayed.") == "Police said the driver stayed."


def test_candidate_regex():
    assert CANDIDATE_RE.search("A cyclist was struck by a car.")
    assert CANDIDATE_RE.search("A truck ran over a pedestrian.")
    assert not CANDIDATE_RE.search("Police closed the road for the investigation.")
