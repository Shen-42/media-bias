"""Codebook v1.1 rules (D-69): charge names, general statements, emergency vehicles,
separate car-only collisions. Bare person nouns were already handled (focus tests)."""

import pytest
import spacy

from nlp import rules


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


def s(nlp, text):
    return next(nlp(text).sents)


def test_charge_name_is_not_accident_term(nlp):
    t = "The driver was charged with failing to remain at the scene of an accident."
    assert not rules.accident_term(s(nlp, t))[0]
    assert rules.accident_term(s(nlp, "A cyclist was killed in an accident with a truck."))[0]


def test_charge_name_is_not_a_collision_noun(nlp):
    t = "The driver was charged with failing to stop after an accident."
    assert not rules.is_crash_sentence(s(nlp, t))[0]
    assert rules.is_crash_sentence(s(nlp, "The driver fled after the accident on Bloor."))[0]


def test_general_statement_is_not_crash_sentence(nlp):
    for t in [
        "There has been a 76 per cent increase in the number of pedestrians struck by drivers.",
        "This is the third fatal collision involving a pedestrian so far in 2025.",
    ]:
        assert not rules.is_crash_sentence(s(nlp, t))[0], t
    assert rules.is_crash_sentence(s(nlp, "A pedestrian was struck by a driver on Tuesday."))[0]


def test_emergency_vehicle_at_scene_is_not_a_road_user(nlp):
    t = "An ambulance arrived at the crash scene minutes later."
    assert not rules.is_crash_sentence(s(nlp, t))[0]
    assert rules.is_crash_sentence(s(nlp, "A pedestrian was struck by an ambulance."))[0]
    assert rules.is_crash_sentence(s(nlp, "A police cruiser hit a cyclist downtown."))[0]


def test_separate_car_only_collision_is_not_crash_sentence(nlp):
    for t in [
        "Police say a vehicle crashed into a pole near the intersection.",
        "The driver then struck a fence and two parked cars.",
    ]:
        assert not rules.is_crash_sentence(s(nlp, t))[0], t
    assert rules.is_crash_sentence(s(nlp, "The SUV crashed into a cyclist near the intersection."))[
        0
    ]
    assert rules.is_crash_sentence(s(nlp, "A man was hit by a car on Queen Street."))[0]
