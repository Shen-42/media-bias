from nlp.article import article_labels, exceptional, overlap_share


def test_exceptional_positive_and_negative():
    assert exceptional("The driver fled the scene.")[0]
    assert exceptional("He was charged with impaired operation.")[0]
    assert not exceptional("The driver was charged with careless driving.")[0]  # HTA (D-12)
    assert not exceptional("The driver remained at the scene.")[0]


def test_overlap_share_null_without_release():
    rows = [{"part": "body", "text_source": "newsroom", "release_sim": None}]
    assert overlap_share(rows) is None
    rows = [
        {"part": "body", "text_source": "police_matched", "release_sim": 0.9},
        {"part": "body", "text_source": "newsroom", "release_sim": 0.2},
        {"part": "body", "text_source": "quoted", "release_sim": 0.9},
    ]
    assert overlap_share(rows) == 0.5


def test_driver_mention_primary_excludes_quotes():
    rows = [
        {"id": "a:b:0", "part": "body", "text_source": "quoted", "is_vru": 0, "release_sim": None},
        {
            "id": "a:b:1",
            "part": "body",
            "text_source": "newsroom",
            "is_vru": 1,
            "release_sim": None,
        },
    ]
    labels = {("a:b:0", "driver_mention", "rule"): "true"}
    out = article_labels({"title": "", "text": ""}, rows, labels)
    assert out["driver_ever_mentioned"][0] is False
    assert out["driver_ever_mentioned_with_quotes"][0] is True
