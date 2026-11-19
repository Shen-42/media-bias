import pytest

from nlp.labeling.nli import HYPOTHESES, decide


def test_every_codebook_label_has_hypotheses():
    assert set(HYPOTHESES) == {
        "voice",
        "driver_reference",
        "focus",
        "vru_as_actor",
        "accident_term",
        "vru_conduct_detail",
        "thematic_cue",
    }
    assert {v for v, _ in HYPOTHESES["voice"]} == {
        "active",
        "passive_with_agent",
        "agentless_passive",
        "intransitive",
        "nominal",
    }


def test_decide_binary_and_categorical():
    assert decide("accident_term", {"true": 0.7}) == ("true", 0.7)
    assert decide("accident_term", {"true": 0.2})[0] == "false"
    assert decide("focus", {"vru": 0.9, "driver": 0.1, "vehicle": 0.3, "other": 0.2})[0] == "vru"


@pytest.mark.models
def test_nli_runs_on_device():
    from common import db
    from nlp.labeling.nli import NLI

    con = db.connect(":memory:")
    s = NLI(con).scores("t1", "A cyclist was not wearing a helmet.", "vru_conduct_detail")
    assert 0 <= s["true"] <= 1
