"""Word lists from codebook.md v1.0. Change the codebook before changing these."""

import re

# Codebook 0 (D-02). Single-word impact verb lemmas.
IMPACT_LEMMAS = {"hit", "strike", "collide", "crash", "pin", "drag", "clip", "door", "ram"}
# Verb + particle/preposition combinations (lemma, particle).
IMPACT_PHRASAL = {
    ("run", "over"),
    ("knock", "down"),
    ("knock", "over"),
    ("mow", "down"),
    ("back", "into"),
    ("plow", "into"),
    ("plough", "into"),
    ("slam", "into"),
    ("smash", "into"),
    ("crash", "into"),
}
# Impact verbs that are transitive (a missing object signals a reduced passive in headlines).
TRANSITIVE_IMPACT = {"hit", "strike", "pin", "drag", "clip", "door", "ram", "run", "knock", "mow"}
# Impact verbs that cannot be passive ("was collided" is ungrammatical).
INTRANSITIVE_IMPACT = {"collide", "crash"}
# Verbs whose struck party is a prepositional object ("crashed into X", "collided with X").
PREP_IMPACT = {
    "collide": {"with"},
    "crash": {"into"},
    "slam": {"into"},
    "smash": {"into"},
    "plow": {"into"},
    "plough": {"into"},
    "back": {"into"},
}

# Codebook 0 (D-03, D-31).
COLLISION_NOUNS = {"crash", "collision", "accident", "hit-and-run"}

VRU_NOUNS = {
    "pedestrian",
    "cyclist",
    "bicyclist",
    "biker",
    "e-biker",
    "rider",
    "scooterist",
    "jogger",
    "runner",
    "walker",
}
DRIVER_NOUNS = {"driver", "motorist", "operator", "trucker", "chauffeur"}
VEHICLE_NOUNS = {
    "car",
    "vehicle",
    "suv",
    "truck",
    "pickup",
    "van",
    "minivan",
    "bus",
    "streetcar",
    "sedan",
    "motorcycle",
    "cab",
    "taxi",
    "jeep",
    "tractor-trailer",
    "trailer",
    "ttc",
    "lorry",
    "auto",
    "automobile",
    "hatchback",
    "coupe",
    "convertible",
    "crossover",
    "ambulance",
    "cruiser",
}
PERSON_NOUNS = {
    "man",
    "woman",
    "boy",
    "girl",
    "child",
    "kid",
    "senior",
    "teen",
    "teenager",
    "person",
    "people",
    "victim",
    "toddler",
    "student",
    "resident",
    "mother",
    "father",
    "grandmother",
    "grandfather",
    "youth",
    "male",
    "female",
    "adult",
    "individual",
}
PRONOUNS = {"he", "she", "they", "him", "her", "them"}
VRU_CONTEXT = re.compile(r"\b(bike|bicycle|e-bike|ebike|scooter|walking|crossing|cycling)\b", re.I)

# Codebook 2.6 (labeling-function lexicon for vru_conduct_detail; not a rule-system label).
CONDUCT_RE = re.compile(
    r"\bhelmet|dark(?:-coloured| colored| coloured)? cloth|dressed in dark|wearing dark"
    r"|headphones|earbuds|on (?:his|her|their) phone|texting|mid-?block|jaywalk"
    r"|outside (?:of )?(?:a|the) crosswalk|not in (?:a|the) crosswalk"
    r"|against (?:the|a) (?:red|light|signal)"
    r"|ran a red|darted|stepped (?:out |off )?into|into the path of|reflective|high-visibility"
    r"|no lights|without lights|intoxicated pedestrian|crossing (?:against|outside)",
    re.I,
)

# Codebook 4.3 (labeling-function lexicon for thematic_cue).
THEMATIC_RE = re.compile(
    r"\bvision zero|this year|so far in 20\d\d|since 20\d\d|statistic|data show|per cent of"
    r"|road design|protected (?:bike )?lane|bike lane|speed limit|traffic calming|safety measure"
    r"|deadliest|road safety|advocat|safer streets|infrastructure|intersection has (?:a )?history"
    r"|calls? for (?:changes|safety|a review)|city council"
    r"|\b\d+(?:st|nd|rd|th) (?:pedestrian|cyclist)"
    r" (?:death|killed|fatality)|pedestrian deaths|cyclist deaths|traffic deaths|fatalities",
    re.I,
)

# Codebook 4.2 (D-12).
FLED_RE = re.compile(
    r"\bfled\b|fail(?:ed|ing|ure)? to (?:remain|stop)|hit-and-run|drove (?:away|off)"
    r"|left the scene|did not remain|didn't remain|took off",
    re.I,
)
IMPAIRED_RE = re.compile(r"\bimpaired|\bimpairment|under the influence|over 80|blood alcohol", re.I)
CRIMINAL_CHARGE_RE = re.compile(
    r"dangerous (?:operation|driving)|criminal negligence|impaired operation|impaired driving"
    r"|manslaughter|stunt driving|street racing|racing",
    re.I,
)
HTA_CHARGE_RE = re.compile(
    r"careless driving|fail(?:ed|ing|ure)? to yield|highway traffic act|\bhta\b|fail to stop for"
    r"|disobey|red light camera",
    re.I,
)

SEVERITY_FATAL_RE = re.compile(
    r"\b(?:died|dies|dead|killed|fatal|fatally|pronounced dead|succumbed|deceased|death)\b", re.I
)
SEVERITY_INJURY_RE = re.compile(
    r"injur|hurt|hospital|trauma centre|wounds|critical condition|serious condition", re.I
)
SEVERITY_NONE_RE = re.compile(
    r"no (?:one|injuries) (?:was )?(?:hurt|injured|reported)|not injured|uninjured|no injuries",
    re.I,
)

SPEECH_VERBS = {
    "say",
    "tell",
    "state",
    "report",
    "allege",
    "confirm",
    "add",
    "note",
    "explain",
    "describe",
    "write",
    "claim",
    "believe",
    "according",
}
