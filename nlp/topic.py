"""Article topic tags for v1.5 (codebook 7.1). Lexical and explainable.

A topic counts when its terms are in the headline, or appear at least twice in the first two
paragraphs (one passing mention is not enough, D-65). A headline that describes a crash keeps
the article out of bike_lane and transit: a crash story that mentions a bike lane or a TTC bus
is a crash story.
"""

import re

BIKE_LANE_RE = re.compile(
    r"\bbike lanes?\b|\bcycle tracks?\b|cycling (?:infrastructure|network|lanes?)|\bbikeways?\b"
    r"|bike network|\bBill 212\b|Reducing Gridlock|(?:protected|separated) (?:bike )?lanes?",
    re.I,
)
TRANSIT_RE = re.compile(
    r"\bTTC\b|\btransit\b|\bsubway\b|\bGO (?:Transit|trains?)\b|\bMetrolinx\b|Ontario Line"
    r"|\bCrosstown\b|\bLRT\b|\bfares?\b|\bridership\b",
    re.I,
)
CRASH_HEADLINE_RE = re.compile(
    r"\b(?:struck|strikes?|hits?|killed|crash(?:es|ed|ing)?|collid\w*|collision|hit-and-run"
    r"|run over|smash\w*|slam\w*|plows?|rams?"
    r"|injured|dies|dead)\b",
    re.I,
)


def _has(rx: re.Pattern, title: str, text: str) -> bool:
    paras = [p for p in text.split("\n") if p.strip()]
    lead = "\n".join(paras[:2])
    return bool(rx.search(title)) or len(rx.findall(lead)) >= 2


def topics(title: str, text: str) -> list[str]:
    """bike_lane and/or transit tags; crash scope comes from collect.crash (Part A)."""
    if CRASH_HEADLINE_RE.search(title):
        return []
    out = []
    if _has(BIKE_LANE_RE, title, text):
        out.append("bike_lane")
    if _has(TRANSIT_RE, title, text):
        out.append("transit")
    return out
