"""French dependency rules for the grammatical labels (codebook §10, D-101).

Same labels and values as nlp/rules.py, on Universal Dependencies parses from
fr_dep_news_trf (nsubj:pass, aux:pass, obl:agent). Every function returns (value, evidence).
"""

import re
from dataclasses import dataclass

from spacy.tokens import Span, Token

IMPACT = {
    "happer", "heurter", "frapper", "percuter", "renverser", "faucher", "écraser", "emboutir",
    "coincer", "traîner", "accrocher", "frôler", "tamponner", "projeter",
}  # fmt: skip
COLLISION_NOUNS = {"collision", "accident", "accrochage", "carambolage", "délit", "impact"}
VRU = {
    "piéton", "piétonne", "cycliste", "trottinette", "vélo", "bicyclette", "marcheur",
    "marcheuse", "écolier", "écolière", "brigadier", "brigadière", "patineur",
}  # fmt: skip
DRIVER = {
    "conducteur", "conductrice", "automobiliste", "chauffeur", "chauffeuse", "camionneur",
    "camionneuse", "chauffard", "motocycliste", "motard",
}  # fmt: skip
VEHICLE = {
    "voiture", "véhicule", "auto", "automobile", "camion", "camionnette", "fourgonnette",
    "vus", "autobus", "bus", "tramway", "train", "moto", "motocyclette", "taxi", "poids",
    "minifourgonnette", "fourgon", "remorque", "semi-remorque", "dépanneuse", "bétonnière",
    "métro", "cube", "pick-up", "suv",
}  # fmt: skip
PERSON = {
    "homme", "femme", "garçon", "fille", "enfant", "adolescent", "adolescente", "aîné", "aînée",
    "personne", "octogénaire", "septuagénaire", "sexagénaire", "quinquagénaire", "victime",
    "jeune", "dame", "monsieur", "bambin", "fillette", "élève", "résident", "résidente",
}  # fmt: skip
PRONOUNS = {"il", "elle", "ils", "elles", "celui-ci", "celle-ci"}
VRU_CONTEXT = re.compile(r"\b(?:à vélo|à bicyclette|à pied|en trottinette|traversait|marchait)\b")
# Candidate filter for parsing (cheap regex before the transformer).
CANDIDATE_RE = re.compile(
    r"\b(?:happ\w*|heurt\w*|frapp\w*|percut\w*|renvers\w*|fauch\w*|écras\w*|embout\w*"
    r"|coinc\w*|traîn\w*|accroch\w*|collision\w*|accident\w*|délit de fuite|carambol\w*)",
    re.I,
)
CHARGE_RE = re.compile(r"délit de fuite|omis de s'arrêter|lieux d'un accident", re.I)


@dataclass
class Impact:
    verb: Token | None
    tokens: list[Token]


def _lemma(t: Token) -> str:
    return t.lemma_.lower()


def category(t: Token) -> str | None:
    w, lem = t.text.lower(), _lemma(t)
    if w in DRIVER or lem in DRIVER:
        return "driver"
    if w in VRU or lem in VRU:
        return "vru"
    if w in VEHICLE or lem in VEHICLE:
        return "vehicle"
    if w in PERSON or lem in PERSON:
        return "person"
    if w in PRONOUNS and t.pos_ == "PRON":
        return "pronoun"
    return None


def _is_collision_verb(t: Token) -> bool:
    """'entrer en collision avec': the collision noun hangs on 'entrer'."""
    return _lemma(t) == "entrer" and any(_lemma(c) == "collision" for c in t.children)


def impact_verbs(sent: Span) -> list[Token]:
    return [
        t
        for t in sent
        if t.pos_ in ("VERB", "ADJ") and (_lemma(t) in IMPACT or _is_collision_verb(t))
    ]


def clause_tokens(verb: Token) -> list[Token]:
    skip: set[int] = set()
    for c in verb.children:
        if c.dep_ in ("conj", "parataxis", "advcl", "cc", "punct") and c.pos_ in ("VERB", "AUX"):
            skip.update(x.i for x in c.subtree)
    toks = [t for t in verb.subtree if t.i not in skip]
    if verb.dep_.startswith("acl") and verb.head.i not in {t.i for t in toks}:
        toks = [verb.head, *toks]  # reduced relative: "piéton happé par …"
    return sorted(toks, key=lambda t: t.i)


def find_impact(sent: Span) -> Impact:
    verbs = impact_verbs(sent)
    if verbs:
        return Impact(verbs[0], clause_tokens(verbs[0]))
    return Impact(None, list(sent))


def has_collision_noun(sent: Span) -> Token | None:
    charged = re.search(r"\baccus", sent.text, re.I)  # "accusé de délit de fuite": a charge
    for t in sent:
        if _lemma(t) in COLLISION_NOUNS and t.pos_ == "NOUN":
            if charged and CHARGE_RE.search(sent.text) and _lemma(t) in ("délit", "accident"):
                continue
            return t
    return None


def _subject(imp: Impact, sent: Span) -> Token | None:
    v = imp.verb
    if v is None:
        root = sent.root
        for c in root.children:
            if c.dep_ in ("nsubj", "nsubj:pass"):
                return c
        return root if root.pos_ in ("NOUN", "PROPN") else None
    for c in v.children:
        if c.dep_ in ("nsubj", "nsubj:pass"):
            return c
    if v.dep_.startswith("acl"):
        return v.head
    h = v
    while h.dep_ in ("conj", "advcl", "xcomp") and h.head.i != h.i:
        h = h.head
        for c in h.children:
            if c.dep_ in ("nsubj", "nsubj:pass"):
                return c
    return None


def _agent(v: Token) -> Token | None:
    return next((c for c in v.children if c.dep_ == "obl:agent"), None)


def _objects(v: Token) -> list[Token]:
    objs = [c for c in v.children if c.dep_ == "obj" and _lemma(c) != "se"]
    if _is_collision_verb(v):
        for c in v.children:
            if _lemma(c) == "collision":
                objs += [g for g in c.children if g.dep_ == "nmod"]
    return objs


def _passive(v: Token) -> bool:
    if any(c.dep_ in ("aux:pass", "nsubj:pass") for c in v.children):
        return True
    # "s'est fait happer": se faire + infinitive is a passive (parsers attach it variously)
    before = [_lemma(t) for t in v.doc[max(0, v.i - 3) : v.i]]
    if "faire" in before and "se" in before:
        return True
    # headline or reduced passive: bare participle ("Piéton happé par une voiture")
    return (
        "Part" in v.morph.get("VerbForm")
        and not any(c.dep_ in ("aux:tense", "nsubj") for c in v.children)
        and not _objects(v)
    )


def voice(sent: Span) -> tuple[str, str]:
    imp = find_impact(sent)
    v = imp.verb
    if v is None:
        noun = has_collision_noun(sent)
        return "nominal", f"pas de verbe d'impact; nom '{noun.text if noun else '?'}'"
    if _is_collision_verb(v):
        return "intransitive", f"'{v.text} en collision'"
    if _passive(v):
        agent = _agent(v)
        if agent is not None:
            return "passive_with_agent", f"passif '{v.text}' + agent '{agent.text}'"
        return "agentless_passive", f"passif '{v.text}', sans agent"
    if any(category(o) for o in _objects(v)):
        return "active", f"actif '{v.text}', objet '{_objects(v)[0].text}'"
    return "intransitive", f"verbe '{v.text}' sans usager heurté en objet"


def focus(sent: Span) -> tuple[str, str]:
    imp = find_impact(sent)
    subj = _subject(imp, sent)
    if subj is None:
        return "other", "pas de sujet usager"
    cat = category(subj)
    if cat in ("vru", "driver", "vehicle"):
        return cat, f"sujet '{subj.text}' ({cat})"
    if cat in ("person", "pronoun"):
        if voice(sent)[0] == "active":
            return "driver", f"sujet '{subj.text}' est la partie qui heurte"
        return "vru", f"sujet '{subj.text}' est la personne heurtée"
    return "other", f"sujet '{subj.text}' n'est pas un usager"


def driver_reference(sent: Span) -> tuple[str, str]:
    imp = find_impact(sent)
    for t in imp.tokens:
        if category(t) == "driver":
            return "person", f"conducteur '{t.text}' dans la proposition d'impact"
    v_label = voice(sent)[0]
    striker = None
    if imp.verb is not None:
        striker = (
            _agent(imp.verb)
            if v_label == "passive_with_agent"
            else (_subject(imp, sent) if v_label == "active" else None)
        )
    if striker is not None and category(striker) in ("person", "pronoun"):
        return "person", f"personne '{striker.text}' heurte"
    for t in imp.tokens:
        if category(t) == "vehicle":
            return "vehicle", f"véhicule '{t.text}' dans la proposition d'impact"
    return "absent", "ni conducteur ni véhicule dans la proposition d'impact"


def vru_as_actor(sent: Span) -> tuple[bool, str]:
    imp = find_impact(sent)
    if imp.verb is None:
        return False, "pas de verbe d'impact"
    if voice(sent)[0] not in ("active", "intransitive"):
        return False, "usager non présenté comme acteur"
    subj = _subject(imp, sent)
    if subj is not None and (
        category(subj) == "vru"
        or (category(subj) in ("person", "pronoun") and VRU_CONTEXT.search(sent.text))
    ):
        return True, f"usager vulnérable '{subj.text}' sujet de '{imp.verb.text}'"
    return False, "sujet non vulnérable"


def accident_term(sent: Span) -> tuple[bool, str]:
    if CHARGE_RE.search(sent.text):
        text = CHARGE_RE.sub("", sent.text)
        if not re.search(r"\baccident", text, re.I):
            return False, "nom d'accusation"
    for t in sent:
        if _lemma(t) == "accident" and t.pos_ == "NOUN":
            return True, f"'{t.text}'"
    return False, "pas d'« accident »"


def is_crash_sentence(sent: Span) -> tuple[bool, str]:
    imp = find_impact(sent)
    cue = imp.verb if imp.verb is not None else has_collision_noun(sent)
    if cue is None:
        return False, "ni verbe d'impact ni nom de collision"
    users = [t for t in sent if category(t)]
    if not users:
        return False, f"indice '{cue.text}' sans usager"
    return True, f"indice '{cue.text}'; usager '{users[0].text}'"


def label_crash_sentence(sent: Span) -> dict[str, tuple]:
    return {
        "voice": voice(sent),
        "driver_reference": driver_reference(sent),
        "focus": focus(sent),
        "vru_as_actor": vru_as_actor(sent),
        "accident_term": accident_term(sent),
    }
