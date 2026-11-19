import pytest
import spacy

from nlp.rules import is_passive


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


def _tok(doc, word):
    return next(t for t in doc if t.text == word)


def test_conj_shares_passive_aux(nlp):
    doc = nlp("The cyclist was struck and dragged for a block.")
    assert is_passive(_tok(doc, "dragged"), False)


def test_conj_with_own_subject_is_not_passive(nlp):
    doc = nlp("The cyclist was struck and the driver dragged her for a block.")
    assert not is_passive(_tok(doc, "dragged"), True)


def test_perfect_is_not_passive(nlp):
    doc = nlp("The driver has struck a pedestrian.")
    assert not is_passive(_tok(doc, "struck"), True)
