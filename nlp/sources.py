"""Quoted sources and their roles for v1.5 (codebook 8.1). Lexical and explainable.

A quote unit is a sentence with a speech verb and a speaker. The speaker comes from the
attribution ("...," Coun. Lee said / said a TTC spokesperson / according to the BIA). A pronoun
speaker reuses the last named speaker in the article; a bare surname takes the role the article
gives that person elsewhere ("Premier Doug Ford" ... "Ford said").
"""

import re

_SPEECH = r"(?:said|says|told|tells|added|adds|noted|explained|wrote|stated|argued|argues|warned)"
_NAME = r"[A-Z][\w.'’-]*(?:\s+[A-Z][\w.'’-]*){0,3}"
_NP = r"(?:[Tt]he |[Aa]n? |[Oo]ne |[A-Z])[\w.,'’ -]{0,60}?"

SPEAKER_PATTERNS = [
    # "...," Coun. Lee said.  /  "...," she said.
    re.compile(rf"[”\"],?\s+(?P<s>{_NAME}|{_NP}|he|she|they)\s+{_SPEECH}\b"),
    # "...," said a rider at Kennedy station.  (only after a quote or comma: D-66)
    re.compile(rf"[”\",]\s*{_SPEECH}\s+(?P<s>{_NP})(?:[.,;]|$)"),
    # according to the Bloor-Annex BIA.
    re.compile(rf"according to (?P<s>{_NP})(?:[.,;]|$)"),
    # The BIA says sales fell ...  /  Asked about the cost, Tran said ...
    re.compile(rf"^(?:[^,]{{0,60}},\s+)?(?P<s>{_NAME}|{_NP}|He|She|They)\s+{_SPEECH}\b"),
]
PRONOUNS = {"he", "she", "they"}
# A speaker phrase never contains a finite verb; one that does is a clause, not a speaker.
CLAUSE_RE = re.compile(r"\b(?:was|were|is|are|has|have|had|will|would|can|could|should)\b", re.I)
LEAD_RE = re.compile(
    r"^(?:In|As|Asked|Discussing|Speaking|Responding|At|On|After|For|When|While)\b[^,]*,\s*"
)

# Checked in order; the first match wins (codebook 8.1 decision rules).
ROLE_CUES = [
    ("politician_city", r"\bCoun\.|\bcouncill?or\b|\bmayor\b|deputy mayor|city council\b"),
    (
        "politician_province",
        r"\bPremier\b|\bMPP\b|\bminist(?:er|ry)\b|Queen's Park|provincial government|the province\b"
        r"|Ford government|\bNDP\b|\bLiberal\b|\bcritic\b|house leader|opposition",
    ),
    ("police", r"\bConst\.|\bSgt\.|\bDet\.|\bInsp\.|\bpolice\b|\bofficer\b"),
    (
        "agency_staff",
        r"\bTTC\b|\bMetrolinx\b|\bcity staff\b|^City staff|City of Toronto|transportation services"
        r"|general manager|\bspokesperson for the city\b|\bthe city\b",
    ),
    (
        "vru_advocate",
        r"Cycle ?Toronto|CycleTO|Walk Toronto|Friends and Families for Safe Streets|Bells on Bloor"
        r"|\badvocat|\bcyclists?\b|\bpedestrians?\b|\bbike rider",
    ),
    (
        "expert",
        r"\bprofessor\b|\bresearcher\b|\bUniversity\b|\bplanner\b|\bengineer\b|\beconomist\b"
        r"|\bexpert\b|\banalyst\b",
    ),
    (
        "business",
        r"\bBIA\b|business (?:owner|association|improvement)|\bowner\b|Chamber of Commerce"
        r"|\bmerchant|\bdeveloper\b|\brestaurant|\bowns\b|\bcaf[eé]\b|\bshop\b|\bstore\b",
    ),
    (
        "driver_group",
        r"\bdrivers?\b|\bmotorists?\b|\bCAA\b|\btaxi\b|\btruck(?:er|ing)\b|\bUber\b|\bLyft\b",
    ),
    ("resident", r"\bresidents?\b|\briders?\b|\bcommuters?\b|\bneighbou?rs?\b|\bparent\b"),
    (
        "other",
        r"\bjudge\b|\bJustice\b|\bcourt\b|\bruling\b|\bunion\b|\bMP\b|\bparamedic|\bfirefighter",
    ),
]
ROLE_RES = [(role, re.compile(rx, re.I)) for role, rx in ROLE_CUES]
TITLE_RE = re.compile(
    r"\b((?i:premier|mayor|councill?or|minister|professor)|Coun\.|MPP|Const\.|Sgt\.|Prof\.)"
    r"\s+(?:[A-Z][a-z]+\s+)?([A-Z][a-z]+)"
)
EDGE_RE = re.compile(r"^(?:But|And|However|Still|Meanwhile|Instead)\b,?\s+|\s+(?:also|later|then)$")


def role_of(speaker: str) -> str:
    # The role named closest to the start wins ("the TTC chair, Coun. Myers": councillor).
    if re.search(r"\bchair\b", speaker) and re.search(r"Coun\.|councill?or", speaker):
        return "politician_city"
    for role, rx in ROLE_RES:
        if rx.search(speaker):
            return role
    return "unknown"


def speaker_of(sentence: str) -> str | None:
    for rx in SPEAKER_PATTERNS:
        m = rx.search(sentence)
        if m:
            sp = EDGE_RE.sub("", LEAD_RE.sub("", m.group("s").strip(" ,")))
            if sp and not CLAUSE_RE.search(sp) and len(sp.split()) <= 10:
                return sp
    return None


def _first_mention_role(name: str, sentences: list[str]) -> str:
    """Role whose cue is nearest the first mention of a bare name (D-66)."""
    for s in sentences:
        i = s.find(name)
        if i < 0:
            continue
        best, best_d = "unknown", 61
        for role, rx in ROLE_RES:
            for m in rx.finditer(s):
                d = i - m.end() if m.end() <= i else m.start() - (i + len(name))
                if 0 <= d < best_d or (m.start() <= i < m.end()):
                    best, best_d = role, max(d, 0)
        return best
    return "unknown"


def article_sources(sentences: list[str]) -> list[tuple[int, str, str]]:
    """(sentence index, speaker, role) for each quote unit in an article."""
    titles = {}
    for s in sentences:
        for m in TITLE_RE.finditer(s):
            titles.setdefault(m.group(2), f"{m.group(1)} {m.group(2)}")
    out, last = [], None
    for i, s in enumerate(sentences):
        sp = speaker_of(s)
        if sp is None:
            continue
        if sp.lower() in PRONOUNS:
            if last is None:
                continue
            sp = last
        elif sp in titles:
            sp = titles[sp]
        role = role_of(sp)
        if role == "unknown" and re.fullmatch(_NAME, sp):
            role = _first_mention_role(sp.split()[-1], sentences)
        out.append((i, sp, role))
        last = sp
    return out
