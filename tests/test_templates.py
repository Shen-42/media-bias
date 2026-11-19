"""Template suite for the grammatical rules (CI: en_core_web_sm; local: en_core_web_trf)."""

import pytest
import spacy

from eval.templates.suite import NOT_CRASH, accident_cases, cases
from nlp import rules


@pytest.fixture(scope="module")
def nlp_sm():
    return spacy.load("en_core_web_sm")


def _labels(nlp, text):
    sent = next(nlp(text).sents)
    return (
        rules.voice(sent)[0],
        rules.driver_reference(sent)[0],
        rules.focus(sent)[0],
        rules.vru_as_actor(sent)[0],
    )


@pytest.mark.parametrize(("text", "expected"), cases())
def test_template_labels_sm(nlp_sm, text, expected):
    assert _labels(nlp_sm, text) == expected


@pytest.mark.parametrize(("text", "expected"), cases())
def test_template_crash_filter_positive(nlp_sm, text, expected):
    assert rules.is_crash_sentence(next(nlp_sm(text).sents))[0]


@pytest.mark.parametrize("text", NOT_CRASH)
def test_template_crash_filter_negative(nlp_sm, text):
    assert not rules.is_crash_sentence(next(nlp_sm(text).sents))[0]


@pytest.mark.parametrize(("text", "expected"), accident_cases())
def test_accident_term(nlp_sm, text, expected):
    assert rules.accident_term(next(nlp_sm(text).sents))[0] is expected


@pytest.mark.models
def test_template_labels_trf():
    nlp = spacy.load("en_core_web_trf")
    failures = [(t, e, _labels(nlp, t)) for t, e in cases() if _labels(nlp, t) != e]
    assert not failures, failures[:10]
