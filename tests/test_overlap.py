from nlp.overlap import char_ngrams, jaccard, split_release, text_source

CFG = {"embed_threshold": 0.8, "char_threshold": 0.3}


def test_text_source_precedence():
    assert text_source(True, 0.99, 0.9, CFG) == "quoted"
    assert text_source(False, 0.95, 0.6, CFG) == "police_matched"
    assert text_source(False, 0.95, 0.1, CFG) == "newsroom"  # paraphrase, little shared wording
    assert text_source(False, None, None, CFG) == "newsroom"  # no linked release


def test_char_jaccard_close_copy_vs_different():
    rel = "It is reported that a vehicle was travelling eastbound and struck a cyclist."
    copy = "A vehicle was travelling eastbound when it struck a cyclist."
    other = "Cyclists have long asked for a protected lane on this stretch."
    g = char_ngrams(rel)
    assert jaccard(char_ngrams(copy), g) > jaccard(char_ngrams(other), g)


def test_split_release():
    parts = split_release("It is reported that a car struck a man. He was taken to hospital.\nok")
    assert parts == ["It is reported that a car struck a man.", "He was taken to hospital."]
