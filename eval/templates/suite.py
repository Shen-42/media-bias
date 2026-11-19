"""Template suite: minimal pairs with labels known by construction (PLAN.md §9.3).

Runs in CI as unit tests for the grammatical rules. Passing it is not an accuracy result.
Expected tuple: (voice, driver_reference, focus, vru_as_actor).
"""

from itertools import product

VRUS = ["pedestrian", "cyclist"]
VEHICLES = ["car", "SUV", "truck", "TTC bus", "streetcar"]
# (past, past participle)
VERBS = [("struck", "struck"), ("hit", "hit"), ("ran over", "run over"), ("pinned", "pinned")]

TEMPLATES = [
    ("A driver {past} a {vru} on Bloor Street.", ("active", "person", "driver", False)),
    ("A {vru} was {pp} by a driver.", ("passive_with_agent", "person", "vru", False)),
    ("A {vru} was {pp} on Queen Street West.", ("agentless_passive", "absent", "vru", False)),
    ("A {veh} {past} a {vru} at Yonge and Eglinton.", ("active", "vehicle", "vehicle", False)),
    ("A {vru} was {pp} by a {veh} in North York.", ("passive_with_agent", "vehicle", "vru", False)),
    ("A {vru} has been {pp} by a {veh}.", ("passive_with_agent", "vehicle", "vru", False)),
    ("Police say a {veh} {past} a {vru}.", ("active", "vehicle", "vehicle", False)),
    ("The driver of a {veh} {past} a {vru}.", ("active", "person", "driver", False)),
    (
        "A {vru} was {pp} and the driver remained at the scene.",
        ("agentless_passive", "absent", "vru", False),
    ),
    ("A {vru} died after being {pp} by a {veh}.", ("passive_with_agent", "vehicle", "vru", False)),
]

# Templates that do not vary the verb.
FIXED = [
    ("A {vru} collided with a {veh} on Harbord Street.", ("active", "vehicle", "vru", True)),
    ("A {vru} and a {veh} collided on Harbord Street.", ("intransitive", "vehicle", "vru", True)),
    ("A {vru} is dead after a collision with a {veh}.", ("nominal", "vehicle", "vru", False)),
    ("A {vru} was killed in an accident with a {veh}.", ("nominal", "vehicle", "vru", False)),
]

NOT_CRASH = [
    "Police closed Bloor Street between Spadina and Bathurst for the investigation.",
    "The victim was taken to a trauma centre with life-threatening injuries.",
    "Anyone with dashcam footage is asked to contact police.",
    "The crash happened around 9 p.m.",
]


def cases() -> list[tuple[str, tuple]]:
    out = []
    for (tmpl, exp), vru, veh, (past, pp) in product(TEMPLATES, VRUS, VEHICLES, VERBS):
        if "{veh}" not in tmpl and veh != VEHICLES[0]:
            continue
        out.append((tmpl.format(vru=vru, veh=veh, past=past, pp=pp), exp))
    for (tmpl, exp), vru, veh in product(FIXED, VRUS, VEHICLES):
        out.append((tmpl.format(vru=vru, veh=veh), exp))
    return out


def accident_cases() -> list[tuple[str, bool]]:
    return [
        ("A cyclist was killed in an accident with a truck on Bloor.", True),
        ("Police say the pedestrian was struck in a hit-and-run accident.", True),
        ("A cyclist was killed in a crash with a truck on Bloor.", False),
        ("He accidentally struck a pedestrian.", False),
    ]
