"""Suggested rewrites for crash sentences, after the Road Collision Reporting Guidelines
(Laker & Active Travel Academy, 2021). These are suggestions, not measured results (D-98).

Each suggestion names the guideline point and, where a safe mechanical rewrite exists, gives
one. Rewrites come from the same dependency parse as the labels; no language model is used.
A rewrite is offered only for simple structures; otherwise the note stands alone.

    python -m nlp.rewrite --article <article_id>
"""

import argparse
import re

from spacy.tokens import Span, Token

from nlp import rules

GUIDE = "Road Collision Reporting Guidelines"
PAST = {"run": "ran", "mown": "mowed", "stricken": "struck", "ridden": "rode"}
OBJECT_PRONOUN = {"he": "him", "she": "her", "they": "them", "i": "me", "we": "us"}
CHARGE_RE = re.compile(r"scene of (?:an|the) accident", re.I)
ACCIDENT_RE = re.compile(r"\b(an? )?(accident)(s?)\b", re.I)


def replace_accident(text: str) -> str:
    def sub(m: re.Match) -> str:
        art = m.group(1)
        new = "crashes" if m.group(3) else "crash"
        if m.group(2)[0].isupper():
            new = new.capitalize()
        if art:
            a = "A" if art[0].isupper() else "a"
            return f"{a} {new}"
        return new

    return ACCIDENT_RE.sub(sub, text)


def _span_text(tokens: list[Token]) -> str:
    return "".join(t.text_with_ws for t in tokens).strip()


def _contiguous(tokens: list[Token]) -> bool:
    idx = [t.i for t in tokens]
    return idx == list(range(min(idx), max(idx) + 1))


def _np(t: Token) -> list[Token]:
    return sorted(t.subtree, key=lambda x: x.i)


def _lower_first(text: str, first: Token) -> str:
    if first.pos_ == "PROPN" or (len(first.text) > 1 and first.text.isupper()):
        return text
    return text[:1].lower() + text[1:]


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


PLURAL_DET = {"both", "two", "three", "several", "multiple"}


def _plural(t: Token) -> bool:
    return (
        t.tag_ in ("NNS", "NNPS")
        or any(c.dep_ == "conj" for c in t.children)
        or any(c.text.lower() in PLURAL_DET for c in t.children)
    )


def _driver_of(t: Token) -> str:
    """'a white truck, which fled' -> 'the driver of a white truck, which fled,'"""
    np_ = _np(t)
    text = _lower_first(_span_text(np_), np_[0])
    if any(x.text == "," for x in np_) and not text.endswith(","):
        text += ","
    return f"the driver{'s' if _plural(t) else ''} of {text}"


def _shared_subject_clause(v: Token, group: list[Token]) -> bool:
    """A coordinated verb outside the rewritten group that shares the subject:
    'was struck but did not suffer injuries' would make the driver the one not injured."""
    ids = {g.i for g in group}
    return any(
        c.dep_ == "conj"
        and c.pos_ in ("VERB", "AUX")
        and c.i not in ids
        and not any(g.dep_.startswith("nsubj") for g in c.children)
        for c in v.children
    )


def _verb_group(v: Token) -> list[Token]:
    """Participle plus its particle and coordinated participles: 'struck and killed'."""
    group = [v] + [c for c in v.children if c.dep_ == "prt"]
    for c in v.children:
        if (
            c.dep_ == "conj"
            and c.tag_ == "VBN"
            and not any(g.dep_.startswith("nsubj") for g in c.children)
        ):
            cc = [x for x in v.children if x.dep_ == "cc" and v.i < x.i < c.i]
            group += cc + [c] + [g for g in c.children if g.dep_ == "prt"]
    group = sorted(group, key=lambda t: t.i)
    return group if _contiguous(group) else [v]


def passive_rewrite(sent: Span) -> str | None:
    """'A cyclist was struck by a car on Bloor.' -> 'The driver of a car struck a cyclist on
    Bloor.' With no agent the striker is 'a driver'."""
    imp = rules.find_impact(sent)
    v = imp.verb
    if v is None or v.tag_ != "VBN":
        return None
    subj = next((c for c in v.children if c.dep_ == "nsubjpass"), None)
    aux = [c for c in v.children if c.dep_ == "auxpass"]
    if (
        subj is None
        or not aux
        or any(a.text.lower() == "being" for a in aux)
        or subj.i > v.i
        or rules.category(subj) not in ("vru", "person", "pronoun")
    ):
        return None
    obj = _np(subj)
    between = [t for t in sent if obj[-1].i < t.i < v.i]
    if not _contiguous(obj) or any(
        t.dep_ not in ("aux", "auxpass", "advmod", "neg") for t in between
    ):
        return None
    adverbs = [t for t in between if t.dep_ in ("advmod", "neg")]
    group = _verb_group(v)
    # the by-agent may hang on the last coordinated verb: "struck and killed by a vehicle"
    agent, by = None, None
    for g in reversed(group):
        agent = rules._agent(g)
        if agent is not None:
            by = next(c for c in g.children if c.dep_ == "agent" or c.text.lower() == "by")
            break
    if agent is not None:
        cat = rules.category(agent)
        agent_text = _lower_first(_span_text(_np(agent)), _np(agent)[0])
        if cat == "vehicle":
            striker = _driver_of(agent)
        elif cat in ("driver", "person", "pronoun"):
            striker = agent_text
        else:
            return None
    else:
        striker = "a driver"
    # "struck while crossing": the subjectless clause would attach to the driver.
    if any(
        c.dep_ in ("advcl", "xcomp") and not any(g.dep_.startswith("nsubj") for g in c.children)
        for c in v.children
    ) or _shared_subject_clause(v, group):
        return None
    skip = {t.i for t in _np(by)} if by is not None else set()
    rest = [t for t in sent if t.i > group[-1].i and t.i not in skip]
    verbs = " ".join(PAST.get(t.text.lower(), t.text) for t in group)
    prefix = _span_text([t for t in sent if t.i < obj[0].i])
    parts = [
        prefix,
        striker if prefix else _cap(striker),
        " ".join(t.text for t in adverbs),
        verbs,
        OBJECT_PRONOUN.get(_span_text(obj).lower()) or _lower_first(_span_text(obj), obj[0]),
    ]
    out = " ".join(p for p in parts if p)
    tail = _span_text(rest)
    if tail and tail[0] not in ".,;:!?":
        out += " "
    return re.sub(r"\s+", " ", out + tail).strip()


def vehicle_subject_rewrite(sent: Span) -> str | None:
    """'A car hit a cyclist.' -> 'The driver of a car hit a cyclist.'"""
    imp = rules.find_impact(sent)
    if imp.verb is None or rules.voice(sent)[0] != "active":
        return None
    subj = rules._subject(imp, sent)
    if subj is None or rules.category(subj) != "vehicle" or subj.head.i != imp.verb.i:
        return None
    if any(rules.category(t) == "driver" for t in sent):
        return None  # the driver is named elsewhere; "the driver of" would repeat them
    if any(c.dep_ == "poss" for c in subj.children) or _shared_subject_clause(imp.verb, [imp.verb]):
        return None  # "his motorcycle": the person named is the driver
    np_ = _np(subj)
    if not _contiguous(np_):
        return None
    before = _span_text([t for t in sent if t.i < np_[0].i])
    after = "".join(t.text_with_ws for t in sent if t.i > np_[-1].i)
    head = _driver_of(subj)
    new = (before + " " + head) if before else _cap(head)
    return (new + " " + after).strip()


def suggest(sent: Span, vru_conduct: bool = False) -> list[dict]:
    """Suggestions for one crash sentence: [{point, note, rewrite}]."""
    out = []
    voice = rules.voice(sent)[0]
    dref = rules.driver_reference(sent)[0]
    # a charge name ("leaving the scene of an accident") is quoted law, not word choice
    has_accident = rules.accident_term(sent)[0] and not CHARGE_RE.search(sent.text)
    rewrite = None
    if voice in ("agentless_passive", "passive_with_agent"):
        rewrite = passive_rewrite(sent)
        out.append(
            {
                "point": "Say who did what: name the driver as the actor",
                "note": "Passive voice puts the person struck first and "
                + (
                    "leaves out who was driving."
                    if voice == "agentless_passive"
                    else "moves the driver or vehicle into a by-phrase."
                ),
                "rewrite": rewrite,
            }
        )
    elif voice in ("intransitive", "nominal"):
        out.append(
            {
                "point": "Say who did what: name the driver as the actor",
                "note": f"The sentence ({voice}) reports a collision without saying a driver "
                "struck someone. If police describe it that way, say so: 'A driver struck …'.",
                "rewrite": None,
            }
        )
    if dref == "vehicle" and voice == "active":
        rewrite = vehicle_subject_rewrite(sent)
        out.append(
            {
                "point": "Refer to the driver, not only the vehicle",
                "note": "The vehicle is the actor; vehicles are driven by people.",
                "rewrite": rewrite,
            }
        )
    if has_accident:
        base = rewrite or sent.text
        out.append(
            {
                "point": "Prefer 'crash' or 'collision' to 'accident'",
                "note": "'Accident' implies no one was at fault before that is known.",
                "rewrite": replace_accident(base),
            }
        )
        if rewrite:
            for s in out[:-1]:
                s["rewrite"] = replace_accident(s["rewrite"]) if s["rewrite"] else None
    if vru_conduct:
        out.append(
            {
                "point": "Avoid details that shift blame without evidence",
                "note": "Helmet, clothing or crossing details belong only if police say they "
                "bear on the crash.",
                "rewrite": None,
            }
        )
    return out


def main() -> None:
    from common import db
    from nlp.sentences import load_models

    ap = argparse.ArgumentParser()
    ap.add_argument("--article", required=True)
    args = ap.parse_args()
    con = db.connect()
    _, nlp = load_models()
    rows = con.execute(
        "SELECT id, text FROM sentences WHERE article_id = ? AND is_crash = 1"
        " AND text_source != 'quoted' ORDER BY idx",  # quotes are the source's words
        (args.article,),
    ).fetchall()
    for sid, text in rows:
        sent = next(nlp(text).sents)
        for s in suggest(sent):
            print(f"{sid}: {text}\n  [{GUIDE}] {s['point']}: {s['note']}")
            if s["rewrite"]:
                print(f"  Suggested: {s['rewrite']}")


if __name__ == "__main__":
    main()
