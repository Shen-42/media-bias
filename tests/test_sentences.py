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


def test_split_never_crosses_paragraphs():
    import spacy

    from nlp.sentences import split

    nlp = spacy.load("en_core_web_sm")
    body = "Elderly man struck near Square One\nA male pedestrian was hit by a car."
    out = [s for s in split(nlp, None, body) if s["part"] == "body"]
    assert [s["text"] for s in out] == [
        "Elderly man struck near Square One",
        "A male pedestrian was hit by a car.",
    ]
    assert body[out[1]["start"] : out[1]["end"]] == out[1]["text"]
