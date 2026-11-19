from nlp.quotes import inside_share, is_attributed, is_quoted, quote_spans


def test_quote_spans_curly_and_straight():
    text = '“The car struck her,” he said. She said "no comment" later.'
    spans = quote_spans(text)
    assert [text[a:b] for a, b in spans] == ["“The car struck her,”", '"no comment"']


def test_unclosed_quote_runs_to_paragraph_end():
    text = "“First paragraph of a long quote.\n“Second paragraph,” she said."
    spans = quote_spans(text)
    assert text[spans[0][0] : spans[0][1]] == "“First paragraph of a long quote."
    assert text[spans[1][0] : spans[1][1]] == "“Second paragraph,”"


def test_is_quoted_by_impact_clause():
    text = "Police said the driver “remained at the scene” after a car hit a cyclist."
    spans = quote_spans(text)
    impact = (text.index("a car hit"), text.index("cyclist") + 7)
    assert not is_quoted(0, len(text), spans, impact)
    text2 = "“A vehicle struck a cyclist,” police said."
    spans2 = quote_spans(text2)
    impact2 = (text2.index("A vehicle"), text2.index("cyclist") + 7)
    assert is_quoted(0, len(text2), spans2, impact2)


def test_is_quoted_by_share_for_non_crash_sentence():
    text = "“It was terrible to see,” a witness said."
    assert is_quoted(0, len(text), quote_spans(text))
    assert inside_share(0, 5, []) == 0.0


def test_attribution_positive_and_negative():
    assert is_attributed("Police say a car struck a cyclist.")
    assert is_attributed("According to police, the driver remained.")
    assert not is_attributed("A car struck a cyclist on Bloor.")
