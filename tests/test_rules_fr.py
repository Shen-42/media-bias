"""French grammatical rules (codebook §10, D-101): a positive and a negative per label."""

import pytest
import spacy

from nlp import rules_fr as R


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("fr_core_news_sm")


def s(nlp, text):
    return next(nlp(text).sents)


def test_crash_sentence(nlp):
    assert R.is_crash_sentence(s(nlp, "Un piéton a été happé par une voiture lundi."))[0]
    assert not R.is_crash_sentence(s(nlp, "La rue est fermée pour l'enquête."))[0]
    assert not R.is_crash_sentence(s(nlp, "Le conducteur a été accusé de délit de fuite."))[0]


def test_voice(nlp):
    assert R.voice(s(nlp, "Un piéton a été happé par une voiture."))[0] == "passive_with_agent"
    assert R.voice(s(nlp, "Une cycliste a été heurtée jeudi soir."))[0] == "agentless_passive"
    assert R.voice(s(nlp, "Un camion a percuté un cycliste."))[0] == "active"
    assert R.voice(s(nlp, "Une cycliste s'est fait frapper sur la rue Rachel."))[0] == (
        "agentless_passive"
    )
    assert R.voice(s(nlp, "Le cycliste est entré en collision avec une voiture."))[0] == (
        "intransitive"
    )
    assert R.voice(s(nlp, "Collision entre un piéton et un autobus"))[0] == "nominal"


def test_driver_reference(nlp):
    assert R.driver_reference(s(nlp, "Un conducteur a happé une piétonne."))[0] == "person"
    assert R.driver_reference(s(nlp, "Un camion a percuté un cycliste."))[0] == "vehicle"
    assert R.driver_reference(s(nlp, "Une cycliste a été heurtée jeudi."))[0] == "absent"


def test_focus(nlp):
    assert R.focus(s(nlp, "Un piéton a été happé par une voiture."))[0] == "vru"
    assert R.focus(s(nlp, "Un camion a percuté un cycliste."))[0] == "vehicle"


def test_vru_as_actor(nlp):
    assert R.vru_as_actor(s(nlp, "Le cycliste est entré en collision avec une voiture."))[0]
    assert not R.vru_as_actor(s(nlp, "Un camion a percuté un cycliste."))[0]


def test_accident_term(nlp):
    assert R.accident_term(s(nlp, "Un accident impliquant une cycliste a eu lieu."))[0]
    assert not R.accident_term(s(nlp, "Une collision impliquant une cycliste a eu lieu."))[0]
