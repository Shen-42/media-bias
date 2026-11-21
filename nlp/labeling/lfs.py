"""Labeling functions for the two fuzzy labels (PLAN.md §9.1). Each returns 1, 0, or ABSTAIN.

Input is a dict with: text, nli (score for the label's "true" hypothesis, or None),
qwen ("true" | "false" | None). Outlet identity is never an input (CLAUDE.md).
"""

import re

from common import config
from nlp.lexicons import CONDUCT_RE, THEMATIC_RE

ABSTAIN, NO, YES = -1, 0, 1

MEDICAL_RE = re.compile(
    r"hospital|injur|pronounced dead|died|trauma centre|paramedic|critical condition", re.I
)
PROCEDURAL_RE = re.compile(
    r"investigat|dashcam|footage|anyone with information|contact police|crime stoppers"
    r"|road(?:s)? (?:was|were|are|is) closed|closures?|reopened|collision reconstruction",
    re.I,
)
EPISODE_RE = re.compile(
    r"\b(?:around|at about|shortly (?:after|before)|just (?:after|before)) \d{1,2}(?::\d\d)?"
    r"|\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.I,
)


def _nli(x: dict, hi: float = 0.8, lo: float = 0.2) -> int:
    s = x.get("nli")
    if s is None:
        return ABSTAIN
    return YES if s >= hi else NO if s <= lo else ABSTAIN


def _qwen(x: dict) -> int:
    return {"true": YES, "false": NO}.get(x.get("qwen"), ABSTAIN)


# vru_conduct_detail
def lf_conduct_lexicon(x):
    return YES if CONDUCT_RE.search(x["text"]) else ABSTAIN


def lf_conduct_medical(x):
    return NO if MEDICAL_RE.search(x["text"]) and not CONDUCT_RE.search(x["text"]) else ABSTAIN


def lf_conduct_procedural(x):
    return NO if PROCEDURAL_RE.search(x["text"]) and not CONDUCT_RE.search(x["text"]) else ABSTAIN


def _hi(label: str) -> float:
    return config.load()["fuzzy"][f"nli_hi_{label}"]


def lf_conduct_nli(x):
    return _nli(x, hi=_hi("vru_conduct_detail"))


def lf_conduct_qwen(x):
    return _qwen(x)


# thematic_cue
def lf_thematic_lexicon(x):
    return YES if THEMATIC_RE.search(x["text"]) else ABSTAIN


def lf_thematic_episode(x):
    return NO if EPISODE_RE.search(x["text"]) and not THEMATIC_RE.search(x["text"]) else ABSTAIN


def lf_thematic_procedural(x):
    return NO if PROCEDURAL_RE.search(x["text"]) and not THEMATIC_RE.search(x["text"]) else ABSTAIN


def lf_thematic_nli(x):
    return _nli(x, hi=_hi("thematic_cue"))


def lf_thematic_qwen(x):
    return _qwen(x)


LFS = {
    "vru_conduct_detail": [
        lf_conduct_lexicon,
        lf_conduct_medical,
        lf_conduct_procedural,
        lf_conduct_nli,
        lf_conduct_qwen,
    ],
    "thematic_cue": [
        lf_thematic_lexicon,
        lf_thematic_episode,
        lf_thematic_procedural,
        lf_thematic_nli,
        lf_thematic_qwen,
    ],
}
