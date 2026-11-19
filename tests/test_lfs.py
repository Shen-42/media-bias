"""Every labeling function: at least one positive (votes) and one negative (abstains/other)."""

from nlp.labeling import lfs
from nlp.labeling.lfs import ABSTAIN, NO, YES


def x(text, nli=None, qwen=None):
    return {"text": text, "nli": nli, "qwen": qwen}


def test_conduct_lexicon():
    assert lfs.lf_conduct_lexicon(x("The cyclist was not wearing a helmet.")) == YES
    assert lfs.lf_conduct_lexicon(x("The cyclist was taken to hospital.")) == ABSTAIN


def test_conduct_medical():
    assert lfs.lf_conduct_medical(x("The cyclist was taken to hospital.")) == NO
    assert lfs.lf_conduct_medical(x("A helmetless cyclist was taken to hospital.")) == ABSTAIN


def test_conduct_procedural():
    assert lfs.lf_conduct_procedural(x("Police are investigating the cyclist crash.")) == NO
    assert lfs.lf_conduct_procedural(x("The cyclist wore dark clothing.")) == ABSTAIN


def test_nli_and_qwen_lfs():
    assert lfs.lf_conduct_nli(x("t", nli=0.9)) == YES
    assert lfs.lf_conduct_nli(x("t", nli=0.1)) == NO
    assert lfs.lf_conduct_nli(x("t", nli=0.5)) == ABSTAIN
    assert lfs.lf_conduct_nli(x("t")) == ABSTAIN
    assert lfs.lf_thematic_qwen(x("t", qwen="true")) == YES
    assert lfs.lf_thematic_qwen(x("t", qwen="false")) == NO
    assert lfs.lf_thematic_qwen(x("t")) == ABSTAIN
    assert lfs.lf_conduct_qwen(x("t", qwen="true")) == YES
    assert lfs.lf_thematic_nli(x("t", nli=0.95)) == YES


def test_thematic_lexicon():
    assert lfs.lf_thematic_lexicon(x("It is the 12th pedestrian death this year.")) == YES
    assert lfs.lf_thematic_lexicon(x("The driver stayed at the scene.")) == ABSTAIN


def test_thematic_episode():
    assert lfs.lf_thematic_episode(x("It happened around 9:30 p.m. on Monday.")) == NO
    assert lfs.lf_thematic_episode(x("Advocates want a protected bike lane on Monday.")) == ABSTAIN


def test_thematic_procedural():
    assert lfs.lf_thematic_procedural(x("Anyone with dashcam footage should call.")) == NO
    assert lfs.lf_thematic_procedural(x("Vision Zero data show deaths rose.")) == ABSTAIN
