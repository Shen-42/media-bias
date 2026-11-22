"""Labeling functions for v1.5 policy frames and stance (codebook 9.1, 9.2; D-60, D-67).

Each LF returns a codebook value or ABSTAIN. Input is a dict with: text, quoted (bool, the
sentence is direct speech), attributed (bool, names a source), nli (value -> score for the
label, or None), qwen (value or None). Outlet identity and source role are never inputs:
stance is reported by source role, so using role as a vote would assume the result (D-67).

The support and oppose cue lists are balanced in size and kind (benefit vs harm, endorse vs
reject), so neither side gets more ways to fire.
"""

import re

ABSTAIN = None

FRAMES = ["economic", "safety", "quality_of_life", "political", "legality", "other", "none"]
INFRA = ["support", "oppose", "none"]
CYCLISTS = ["positive", "negative", "none"]
TRANSIT = ["support", "oppose", "none"]
V15_LABELS = {
    "policy_frame": FRAMES,
    "stance_infrastructure": INFRA,
    "stance_cyclists": CYCLISTS,
    "stance_transit": TRANSIT,
}

FRAME_RES = {
    "economic": re.compile(
        r"\$\s?\d|\bcosts?\b|\bbudget|\bfund(?:ing|ed|s)?\b|\bmillion\b|\bbillion\b|\brevenue"
        r"|\btax(?:es|payers?)?\b|\bsales\b|\bjobs?\b|\beconom",
        re.I,
    ),
    "safety": re.compile(
        r"\bsafe(?:ty|r|ly)?\b|\binjur|\bdeaths?\b|\bkilled\b|\bfatal|\bcollisions?\b|\bcrash"
        r"|\brisk|\bdanger",
        re.I,
    ),
    "quality_of_life": re.compile(
        r"\bcongest|\bgridlock\b|\bcommut|\btraffic\b|travel times?|\bdelays?\b|\bnoise\b"
        r"|\bconvenien|\bwait times?\b|\bcrowd",
        re.I,
    ),
    "political": re.compile(
        r"\belection|\bcampaign|\bvoters?\b|\bparty\b|\bpolitic|\bjurisdiction|\boverreach"
        r"|\bcouncil (?:voted|vote)\b|\bthe premier\b|Ford government",
        re.I,
    ),
    "legality": re.compile(
        r"\bcourt\b|\bCharter\b|\bunconstitutional|\bconstitution|\bruling\b|\bjudge\b"
        r"|\blawsuit|\binjunction|\bappeal\b|\blegislation\b|\bBill 212\b|\bthe Act\b"
        r"|environmental assessment",
        re.I,
    ),
    # Other Boydstun frames (codebook 9.1): capacity and resources, policy evaluation,
    # fairness, public opinion. Added after dev showed no LF voted `other` (D-78).
    "other": re.compile(
        r"\breliab|\bmaintenance\b|\bbreakdowns?\b|\bridership\b|\bcapacity\b|\bstaffing\b"
        r"|\breview\b|\binquiry\b|\baudit\b|\boversight\b|\baccountab|\bpoll\b|\bsurvey\b"
        r"|\bfair(?:ness)?\b|\bequity\b|\bmental health\b|\bhousing\b|\bhomeless",
        re.I,
    ),
}
SCHEDULE_RE = re.compile(
    r"\b(?:will (?:begin|start|close|reopen|resume)|begins?|starts?|is closed|reopens?)\b"
    r"|\b\d{1,2}(?::\d\d)? ?[ap]\.?m\.?",
    re.I,
)

INFRA_TARGET = re.compile(
    r"\bbike lanes?\b|\bcycle tracks?\b|\bbikeways?\b|cycling (?:infrastructure|network|lanes?)"
    r"|\b(?:protected|separated) lanes?\b|\b(?:the|these|those) lanes\b",
    re.I,
)
CYCLIST_TARGET = re.compile(r"\bcyclists?\b|\bbike riders?\b|\bpeople on bikes\b", re.I)
TRANSIT_TARGET = re.compile(
    r"\btransit\b|\bsubway\b|\bTTC\b|\bLRT\b|Ontario Line|\bCrosstown\b|\bextension\b"
    r"|\bGO (?:Transit|trains?)\b|\bthe line\b",
    re.I,
)

# Evaluative cues, paired by kind (benefit / harm, endorse / reject).
SUPPORT_RE = re.compile(
    r"\bsave lives\b|\bsafer\b|\bwelcome[sd]?\b|\bsupports?\b|\bin favour\b"
    r"|\bneeds? (?:this|these|more)|\bbenefits?\b|\bsuccess\b|\bfinally\b|\bworks?\b(?= well)",
    re.I,
)
OPPOSE_RE = re.compile(
    r"\bchok(?:e|ed|ing)\b|\bdisaster\b|\bwaste\b|\boppos(?:e|es|ed)\b|\bagainst\b|\bharms?\b"
    r"|\bfail(?:ure|ed|s)?\b|\bmess\b|\bnightmare\b|\bkill(?:ing)? business",
    re.I,
)
CYCLIST_POS_RE = re.compile(
    r"follow the rules|as much right|right to the road|law-abiding|just want to get home"
    r"|deserve",
    re.I,
)
CYCLIST_NEG_RE = re.compile(
    r"blow (?:through|past)|run(?:ning)? red lights|reckless|entitled|think (?:the road|they own)"
    r"|scofflaw|ignore the rules|menace",
    re.I,
)


def _nli(x: dict, label: str, hi: float = 0.8) -> str | None:
    scores = x.get("nli")
    if not scores:
        return ABSTAIN
    best = max(scores, key=scores.get)
    return best if scores[best] >= hi else ABSTAIN


def _qwen(x: dict) -> str | None:
    return x.get("qwen") or ABSTAIN


# policy_frame
def lf_frame_lexicon(x):
    hits = [f for f, rx in FRAME_RES.items() if rx.search(x["text"])]
    return hits[0] if len(hits) == 1 else ABSTAIN


def lf_frame_schedule_none(x):
    t = x["text"]
    if SCHEDULE_RE.search(t) and not any(rx.search(t) for rx in FRAME_RES.values()):
        return "none"
    return ABSTAIN


def lf_frame_nli(x):
    return _nli(x, "policy_frame")


def lf_frame_qwen(x):
    return _qwen(x)


# shared stance rules
def _no_target(target: re.Pattern):
    def lf(x):
        return "none" if not target.search(x["text"]) else ABSTAIN

    return lf


def _cues(target: re.Pattern, pos: re.Pattern, neg: re.Pattern, pv: str, nv: str):
    def lf(x):
        t = x["text"]
        if not target.search(t):
            return ABSTAIN
        p, n = bool(pos.search(t)), bool(neg.search(t))
        if p == n:
            return ABSTAIN
        # Attributed positions count as stance (codebook 9.2, D-81).
        return pv if p else nv

    return lf


def _no_cue(target: re.Pattern):
    """Target named but no evaluative word: none (codebook 9.2 needs an evaluation; D-83)."""

    def lf(x):
        t = x["text"]
        if not target.search(t) or SUPPORT_RE.search(t) or OPPOSE_RE.search(t):
            return ABSTAIN
        return "none"

    return lf


lf_infra_no_target = _no_target(INFRA_TARGET)
lf_infra_no_cue = _no_cue(INFRA_TARGET)
lf_infra_cues = _cues(INFRA_TARGET, SUPPORT_RE, OPPOSE_RE, "support", "oppose")


def lf_infra_nli(x):
    return _nli(x, "stance_infrastructure")


lf_cyclists_no_target = _no_target(CYCLIST_TARGET)
lf_cyclists_cues = _cues(CYCLIST_TARGET, CYCLIST_POS_RE, CYCLIST_NEG_RE, "positive", "negative")


def lf_cyclists_nli(x):
    return _nli(x, "stance_cyclists")


def lf_cyclists_qwen(x):
    return _qwen(x)


lf_transit_no_target = _no_target(TRANSIT_TARGET)
lf_transit_no_cue = _no_cue(TRANSIT_TARGET)
lf_transit_cues = _cues(TRANSIT_TARGET, SUPPORT_RE, OPPOSE_RE, "support", "oppose")


def lf_transit_nli(x):
    return _nli(x, "stance_transit")


def lf_transit_qwen(x):
    return _qwen(x)


# The support/oppose cue LFs are scored as the lexicon baseline but are not Snorkel inputs:
# on dev they were right on 17% (infrastructure) and 25% (transit) of their votes, mostly
# by misreading "oppose the removal" (D-83). The cyclist cues keep their place.
LFS = {
    "policy_frame": [lf_frame_lexicon, lf_frame_schedule_none, lf_frame_nli, lf_frame_qwen],
    "stance_infrastructure": [
        lf_infra_no_target,
        lf_infra_no_cue,
        lf_infra_nli,
        # no Qwen vote: it reads removal plans and "against the removal" as oppose (D-89)
    ],
    "stance_cyclists": [
        lf_cyclists_no_target,
        lf_cyclists_cues,
        lf_cyclists_nli,
        lf_cyclists_qwen,
    ],
    "stance_transit": [
        lf_transit_no_target,
        lf_transit_no_cue,
        lf_transit_nli,
        lf_transit_qwen,
    ],
}
