"""Rewrite suggestions (D-98). Positive and negative cases per rewrite rule."""

import pytest
import spacy

from nlp import rewrite as R


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


def rw(nlp, text):
    out = [s["rewrite"] for s in R.suggest(next(nlp(text).sents)) if s["rewrite"]]
    return out[-1] if out else None


def test_replace_accident_keeps_article_and_case():
    assert R.replace_accident("It was an accident.") == "It was a crash."
    assert R.replace_accident("Accidents happen") == "Crashes happen"
    assert R.replace_accident("no accidental match") == "no accidental match"


def test_agentless_passive_gets_a_driver(nlp):
    assert rw(nlp, "A pedestrian was struck on Bloor Street.") == (
        "A driver struck a pedestrian on Bloor Street."
    )


def test_vehicle_agent_becomes_driver_of_vehicle(nlp):
    assert rw(nlp, "A cyclist was hit by a car.") == "The driver of a car hit a cyclist."


def test_pronoun_object_case(nlp):
    out = rw(nlp, "A man is in hospital after he was struck by a vehicle.")
    assert out == "A man is in hospital after the driver of a vehicle struck him."


def test_vehicle_subject_rewrite(nlp):
    assert rw(nlp, "A truck struck a cyclist on King Street.") == (
        "The driver of a truck struck a cyclist on King Street."
    )


def test_no_rewrite_when_clause_shares_the_subject(nlp):
    # the driver would become the one who "did not suffer injuries"
    assert rw(nlp, "A woman was struck but did not suffer injuries.") is None


def test_no_rewrite_for_possessed_vehicle_or_named_driver(nlp):
    assert rw(nlp, "A man died after his motorcycle hit a cyclist.") is None
    t = "The car hit her as the driver was turning left."
    assert rw(nlp, t) is None


def test_charge_name_is_left_alone(nlp):
    t = "He was charged with leaving the scene of an accident."
    assert not any("accident" in s["point"] for s in R.suggest(next(nlp(t).sents)))


def test_intransitive_gets_a_note_without_rewrite(nlp):
    sg = R.suggest(next(nlp("A cyclist and a car collided on Queen Street.").sents))
    assert sg and all(s["rewrite"] is None for s in sg)
