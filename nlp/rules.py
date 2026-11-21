"""Dependency rules for the grammatical labels (codebook.md §1.1, §2.1–2.5).

Every function takes a parsed spaCy sentence (Span or Doc) and returns (value, evidence).
Evidence names the rule and the matched tokens so the dashboard can show why.
"""

from dataclasses import dataclass

from spacy.tokens import Span, Token

from nlp import lexicons as lx

SEPARATE_CLAUSE_DEPS = {"conj", "parataxis", "advcl", "cc", "punct"}


@dataclass
class Impact:
    verb: Token | None  # impact verb token, or None for nominal sentences
    particle: str | None
    tokens: list[Token]  # tokens of the impact clause


def _lower(t: Token) -> str:
    return t.text.lower()


def _lemma(t: Token) -> str:
    return t.lemma_.lower()


def _is_hyphen_compound(t: Token) -> bool:
    """'hit' inside 'hit-and-run' is part of a noun, not an impact verb."""
    doc = t.doc
    nxt = doc[t.i + 1] if t.i + 1 < len(doc) else None
    prv = doc[t.i - 1] if t.i > 0 else None
    return (nxt is not None and nxt.text == "-") or (prv is not None and prv.text == "-")


def _particle(t: Token) -> str | None:
    for c in t.children:
        if c.dep_ in ("prt", "prep", "advmod") and (_lemma(t), _lower(c)) in lx.IMPACT_PHRASAL:
            return _lower(c)
    return None


def impact_verbs(sent: Span) -> list[tuple[Token, str | None]]:
    out = []
    for t in sent:
        if t.pos_ not in ("VERB", "AUX") and not (t.tag_ in ("VBN", "VBD") and t.pos_ == "ADJ"):
            continue
        if _is_hyphen_compound(t):
            continue
        prt = _particle(t)
        if _lemma(t) in lx.IMPACT_LEMMAS or prt:
            if _lemma(t) == "back" and not prt:
                continue
            out.append((t, prt))
    return out


def clause_tokens(verb: Token) -> list[Token]:
    """Subtree of the impact verb minus coordinated or adverbial clauses with their own verb."""
    skip: set[int] = set()
    for c in verb.children:
        if c.dep_ in SEPARATE_CLAUSE_DEPS and (c.pos_ in ("VERB", "AUX") or c.dep_ == "cc"):
            skip.update(x.i for x in c.subtree)
    toks = [t for t in verb.subtree if t.i not in skip]
    if verb.dep_ in ("acl", "relcl") and verb.head.i not in {t.i for t in toks}:
        toks = [verb.head, *toks]  # reduced relative: the head noun is the struck party
    return sorted(toks, key=lambda t: t.i)


def find_impact(sent: Span) -> Impact:
    verbs = impact_verbs(sent)
    if verbs:
        v, prt = verbs[0]
        return Impact(v, prt, clause_tokens(v))
    return Impact(None, None, list(sent))


def _in_charge_name(t: Token) -> bool:
    """'failing to remain at the scene of an accident' is a charge name (D-69)."""
    sent = t.sent
    off = t.idx - sent.start_char
    return any(m.start() <= off < m.end() for m in lx.CHARGE_ACCIDENT_RE.finditer(sent.text))


def has_collision_noun(sent: Span) -> Token | None:
    for t in sent:
        if _in_charge_name(t):
            continue
        if _lower(t) in lx.COLLISION_NOUNS or _lemma(t) in lx.COLLISION_NOUNS:
            if t.pos_ in ("NOUN", "PROPN") or _lower(t) == "hit-and-run":
                return t
    text = sent.text.lower()
    if "hit-and-run" in text or "hit and run" in text:
        return sent[0]
    return None


def category(t: Token) -> str | None:
    """Road-user category of a noun token: vru | driver | vehicle | person | pronoun."""
    w, lem = _lower(t), _lemma(t)
    if w in lx.DRIVER_NOUNS or lem in lx.DRIVER_NOUNS:
        return "driver"
    if w in lx.VRU_NOUNS or lem in lx.VRU_NOUNS:
        return "vru"
    if w in lx.VEHICLE_NOUNS or lem in lx.VEHICLE_NOUNS:
        return "vehicle"
    if w in lx.PERSON_NOUNS or lem in lx.PERSON_NOUNS:
        return "person"
    if w in lx.PRONOUNS:
        return "pronoun"
    return None


def _has_driving_modifier(t: Token) -> bool:
    return any(c.dep_ in ("acl", "relcl") and _lemma(c) == "drive" for c in t.children)


def road_user_tokens(tokens) -> list[Token]:
    return [t for t in tokens if category(t)]


def _parties(imp: Impact) -> list[Token]:
    """Subject, objects and agent of the impact verb."""
    v = imp.verb
    if v is None:
        return []
    subj = [c for c in v.children if c.dep_ in ("nsubj", "nsubjpass")]
    return subj + _objects(v) + [a for a in [_agent(v)] if a is not None]


def _separate_collision(imp: Impact, sent: Span) -> bool:
    """A vehicle hits an object or parked car and no VRU or person is named (D-69)."""
    if imp.verb is None or any(category(t) in ("vru", "person", "pronoun") for t in sent):
        return False
    objs = _objects(imp.verb)
    return bool(objs) and all(
        category(o) is None or any(_lower(c) == "parked" for c in o.children) for o in objs
    )


def is_crash_sentence(sent: Span) -> tuple[bool, str]:
    imp = find_impact(sent)
    cue = imp.verb if imp.verb is not None else has_collision_noun(sent)
    if cue is None:
        return False, "no impact verb or collision noun"
    if lx.GENERAL_RE.search(sent.text):
        return False, "general statement about crashes (D-69)"
    parties = _parties(imp)
    users = [
        t
        for t in road_user_tokens(sent)
        if _lower(t) not in lx.EMERGENCY_NOUNS or t in parties  # D-69
    ]
    if not users:
        return False, f"cue '{cue.text}' but no road user"
    if _separate_collision(imp, sent):
        return False, "separate collision with no VRU (D-69)"
    return True, f"cue '{cue.text}'; road user '{users[0].text}'"


def _subject(imp: Impact, sent: Span) -> Token | None:
    v = imp.verb
    if v is None:
        root = sent.root
        for c in root.children:
            if c.dep_ in ("nsubj", "nsubjpass", "expl"):
                return c
        return root if root.pos_ in ("NOUN", "PROPN") else None
    for c in v.children:
        if c.dep_ in ("nsubj", "nsubjpass", "csubj", "expl"):
            return c
    if v.dep_ in ("acl", "relcl"):
        # "A cyclist and a car collided" misparsed as acl of "car": use the first conjunct.
        return v.head.head if v.head.dep_ == "conj" else v.head
    # Shared or implicit subject: "A car swerved and hit a cyclist" (conj),
    # "A cyclist died after being struck" (pcomp/advcl/xcomp): climb to the governing verb.
    h = v
    while h.dep_ in ("conj", "pcomp", "advcl", "xcomp", "pobj", "prep") and h.head is not h:
        h = h.head
        for c in h.children:
            if c.dep_ in ("nsubj", "nsubjpass"):
                return c
    return None


def _objects(v: Token) -> list[Token]:
    objs = [c for c in v.children if c.dep_ in ("dobj", "obj", "dative")]
    for c in v.children:
        phrasal = (_lemma(v), _lower(c)) in lx.IMPACT_PHRASAL
        if c.dep_ in ("prep", "prt") and (
            phrasal or _lower(c) in lx.PREP_IMPACT.get(_lemma(v), ())
        ):
            objs += [g for g in c.children if g.dep_ == "pobj"]
    return objs


def _agent(v: Token) -> Token | None:
    for c in v.children:
        if c.dep_ == "agent" or (c.dep_ == "prep" and _lower(c) == "by"):
            for g in c.children:
                if g.dep_ == "pobj":
                    return g
    return None


def _is_user(t: Token | None) -> bool:
    return t is not None and category(t) is not None


def is_passive(v: Token, has_object: bool) -> bool:
    """Passive marking on a verb: aux/subject passive deps, or a reduced participle clause."""
    deps = {c.dep_ for c in v.children}
    if deps & {"auxpass", "nsubjpass", "csubjpass"}:
        return True
    if v.tag_ == "VBN" and v.dep_ in ("acl", "advcl", "pcomp", "xcomp") and not has_object:
        return True
    # "was struck and dragged": a bare VBN conjunct shares the head's passive auxiliary.
    return (
        v.tag_ == "VBN"
        and v.dep_ == "conj"
        and not has_object
        and not deps & {"nsubj", "aux"}
        and v.head.pos_ in ("VERB", "AUX")
        and is_passive(v.head, False)
    )


def voice(sent: Span) -> tuple[str, str]:
    imp = find_impact(sent)
    v = imp.verb
    if v is None:
        noun = has_collision_noun(sent)
        return "nominal", f"no impact verb; collision noun '{noun.text if noun else '?'}'"
    agent = _agent(v)
    objs = [o for o in _objects(v) if _is_user(o)]
    subj = _subject(imp, sent)
    passive_marked = _lemma(v) not in lx.INTRANSITIVE_IMPACT and is_passive(v, bool(objs))
    # Headline reduced passive: "Cyclist struck on Bloor" parsed as active with no object.
    base = _lemma(v)
    reduced = (
        not passive_marked
        and base in lx.TRANSITIVE_IMPACT
        and imp.particle is None
        and not objs
        and not any(c.dep_ in ("dobj", "obj") for c in v.children)
        and subj is not None
        and category(subj) in ("vru", "person", "pronoun")
    )
    if passive_marked or reduced or (agent is not None and not objs):
        if agent is not None:
            return "passive_with_agent", f"passive '{v.text}' + by-agent '{agent.text}'"
        return "agentless_passive", f"passive '{v.text}', no by-agent" + (
            " (reduced headline passive)" if reduced else ""
        )
    if objs:
        return "active", f"active '{v.text}' with struck party '{objs[0].text}'"
    return "intransitive", f"impact verb '{v.text}' with no struck road user as object"


def focus(sent: Span) -> tuple[str, str]:
    imp = find_impact(sent)
    subj = _subject(imp, sent)
    if subj is None or subj.dep_ == "expl":
        return "other", "no road-user subject"
    # spaCy heads: "the driver of a pickup" -> driver; "a cyclist and a car" -> cyclist.
    cat = category(subj)
    if cat == "vru":
        return "vru", f"subject '{subj.text}' is a VRU"
    if cat == "driver":
        return "driver", f"subject '{subj.text}' is a driver"
    if cat == "vehicle":
        return "vehicle", f"subject '{subj.text}' is a vehicle"
    if cat in ("person", "pronoun"):
        v, _ = voice(sent)
        if _has_driving_modifier(subj) or (v == "active" and imp.verb is not None):
            return "driver", f"subject '{subj.text}' is the striking person"
        return "vru", f"subject '{subj.text}' is the struck person"
    return "other", f"subject '{subj.text}' is not a road user"


def driver_reference(sent: Span) -> tuple[str, str]:
    imp = find_impact(sent)
    toks = imp.tokens
    v, _ = voice(sent)
    subj = _subject(imp, sent)
    agent = _agent(imp.verb) if imp.verb is not None else None
    for t in toks:
        if category(t) == "driver":
            return "person", f"driver noun '{t.text}' in impact clause"
        if category(t) in ("person", "pronoun") and _has_driving_modifier(t):
            return "person", f"'{t.text} driving …' in impact clause"
    striker = agent if v == "passive_with_agent" else (subj if v == "active" else None)
    if striker is not None and category(striker) in ("person", "pronoun"):
        return "person", f"person '{striker.text}' is the striking party"
    for t in toks:
        if category(t) == "vehicle":
            return "vehicle", f"vehicle noun '{t.text}' in impact clause"
    return "absent", "no driver or vehicle in impact clause"


def _vru_like(t: Token) -> bool:
    if category(t) == "vru":
        return True
    if category(t) in ("person", "pronoun"):
        return bool(lx.VRU_CONTEXT.search(" ".join(x.text for x in t.subtree)))
    return False


def vru_as_actor(sent: Span) -> tuple[bool, str]:
    # "pedestrian in collision with vehicle"
    for t in sent:
        if (
            _lower(t) == "in"
            and t.i + 1 < len(sent.doc)
            and _lower(sent.doc[t.i + 1]) == "collision"
        ):
            if _vru_like(t.head):
                return True, f"VRU '{t.head.text}' + 'in collision with'"
    imp = find_impact(sent)
    v = imp.verb
    if v is None:
        return False, "no impact verb"
    vo, _ = voice(sent)
    if vo not in ("active", "intransitive"):
        return False, f"VRU not presented as actor (voice {vo})"
    subj = _subject(imp, sent)
    if subj is not None and _vru_like(subj):
        return True, f"VRU '{subj.text}' is subject of '{v.text}'"
    return False, "subject is not a VRU"


def accident_term(sent: Span) -> tuple[bool, str]:
    for t in sent:
        if _lemma(t) == "accident" and t.pos_ == "NOUN" and not _in_charge_name(t):
            return True, f"'{t.text}'"
    return False, "no 'accident'"


def label_crash_sentence(sent: Span) -> dict[str, tuple]:
    return {
        "voice": voice(sent),
        "driver_reference": driver_reference(sent),
        "focus": focus(sent),
        "vru_as_actor": vru_as_actor(sent),
        "accident_term": accident_term(sent),
    }
