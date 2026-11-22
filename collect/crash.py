"""Article metadata, crash linking and police-release linking (PLAN.md §6 steps 4, 5, 7).

Runs after nlp.sentences (it needs crash sentences). All rules are lexical and explainable.
"""

import argparse
import json
import re
from datetime import date

from common import config, db
from nlp import lexicons as lx

OTHER_POLICE_RE = re.compile(
    r"peel (?:regional )?police|york (?:regional )?police|durham (?:regional )?police"
    r"|halton (?:regional )?police|hamilton police|ontario provincial police|\bopp\b"
    r"|niagara (?:regional )?police|waterloo (?:regional )?police|ottawa police|guelph police",
    re.I,
)
TORONTO_POLICE_RE = re.compile(r"toronto police|\btps\b|toronto paramedic", re.I)
OTHER_CITY_RE = re.compile(
    r"\b(?:mississauga|brampton|vaughan|markham|pickering|oshawa|ajax|whitby|richmond hill"
    r"|oakville|burlington|hamilton|caledon|newmarket|aurora|milton|barrie|ottawa|montreal"
    r"|vancouver|calgary|london, ont|kitchener|waterloo|windsor|clarington|georgina)\b",
    re.I,
)
_US_STATES = (
    "Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia"
    "|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland"
    "|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada"
    "|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma"
    "|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah"
    "|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming"
)
# A place outside Toronto in the lead of a local-section article (D-54).
ELSEWHERE_RE = re.compile(
    rf"\b(?:{_US_STATES}|U\.S\.|United States|Quebec|British Columbia|B\.C\.|Alberta"
    r"|Saskatchewan|Manitoba|Nova Scotia|New Brunswick|Newfoundland|Prince Edward Island"
    r"|England|U\.K\.|France|Germany|Australia|India|China|Mexico|Niagara)(?![a-z])"
    r"|\b[A-Z][a-z]+(?: [A-Z][a-z]+)?, (?:Ont|Que)\."
)
GLOBAL_SECTION_RE = re.compile(r" - ([^|]+?) \| Global")  # "Title - Okanagan | Globalnews.ca"
WIRE_RE = re.compile(r"Associated Press|\(AP\)|\bAP\b|Reuters")
TORONTO_SIGNAL_RE = re.compile(
    r"Toronto|\bTPS\b|\bTTC\b|Etobicoke|Scarborough|North York|East York"
)
VRU_WORD_RE = re.compile(r"\b(pedestrian|cyclist|bicyclist|e-?bike|bike|bicycle|scooter)s?\b", re.I)
# A person struck by a vehicle with no occupant cue is treated as a pedestrian (D-39).
PERSON_RE = re.compile(
    r"\b(?:man|woman|men|women|people|boy|girl|child|senior|teen|teenager|person|toddler"
    r"|student|\d+-year-old)s?\b",
    re.I,
)
OCCUPANT_RE = re.compile(
    r"driver of|his car|her car|their car|passenger|behind the wheel|inside the vehicle"
    r"|occupants?|motorcyclist",
    re.I,
)
_PERSON = PERSON_RE.pattern[2:-2]
_STRIKE = r"(?:struck|hit|run over|ran over|mowed down|pinned|dragged|killed by)"
# D-54: the person must be the one struck: a passive strike verb after the person
# ("a boy suffered injuries after he was hit") or an active one right before ("ran over a woman").
STRUCK_PERSON_RE = re.compile(
    rf"\b{_PERSON}\b[^.;]{{0,80}}?\b(?:was|were|been|being|is|are)\s+(?:\w+ly\s+)?{_STRIKE}\b"
    rf"|\b{_PERSON}\b[^.;]{{0,20}}?\b(?:\w+ly\s+)?{_STRIKE}\s+(?:by|during|in|while|on|at)\b"
    rf"|\b{_STRIKE}\b[^.;]{{0,25}}?\b{_PERSON}\b",
    re.I,
)
MOTOR_RE = re.compile(
    r"\b(?:driver|motorist|car|vehicle|suv|truck|pickup|van|bus|streetcar|sedan|taxi"
    r"|motorcycle|tractor-trailer|minivan|jeep|hit-and-run)s?\b",
    re.I,
)
ROUNDUP_RE = re.compile(
    r"separate (?:collisions|crashes|incidents)|two (?:separate )?(?:collisions|crashes)"
    r"|several (?:collisions|crashes)|multiple (?:collisions|crashes)",
    re.I,
)
FOLLOW_UP_RE = re.compile(
    r"\bcharged\b|\bidentified\b|\bvigil\b|\bcourt\b|\bsentenced\b|\bmemorial\b|ghost bike"
    r"|\bguilty\b|\bfamily of\b|\bremembered\b|\bmourn|\barrested\b|\bsurrender",
    re.I,
)
STREET_SUFFIX = (
    r"Street|St\.|Avenue|Ave\.|Road|Rd\.|Drive|Dr\.|Boulevard|Blvd\.|Crescent|Lane|Way"
    r"|Parkway|Trail|Court|Place|Circle|Gate|Terrace|Expressway|Highway|Square"
)
STREET_RE = re.compile(rf"\b((?:[A-Z][a-zA-Z'\.]+ ){{1,3}})(?:{STREET_SUFFIX})\b")
INTERSECTION_RE = re.compile(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)?) and ([A-Z][a-z]+(?: [A-Z][a-z]+)?)")
STOP_STREET = {"The", "A", "An", "In", "On", "At", "Police", "Toronto", "North", "South"}


LOCAL_OUTLETS = {"citynews", "ctv"}  # Toronto-section sites; Global is national (D-40)


def is_toronto(title: str, text: str, local: bool = False) -> bool:
    blob = f"{title}\n{text}"
    if OTHER_POLICE_RE.search(blob) and not TORONTO_POLICE_RE.search(blob):
        return False
    if TORONTO_POLICE_RE.search(blob):
        return True
    lead = f"{title}\n{text[:400]}"
    if OTHER_CITY_RE.search(lead):
        return False
    if not local:
        # D-58: a non-Toronto regional section, or a place elsewhere in the lead, is out.
        section = GLOBAL_SECTION_RE.search(title)
        if section and section.group(1).strip() != "Toronto":
            return False
        return "Toronto" in blob and not (section is None and ELSEWHERE_RE.search(lead))
    # Local sections also carry wire copy (D-54).
    if TORONTO_SIGNAL_RE.search(blob):
        return True
    return not (ELSEWHERE_RE.search(lead) or WIRE_RE.search(text))


def severity(title: str, text: str) -> str:
    lead = f"{title}\n{text[:1200]}"
    if lx.SEVERITY_FATAL_RE.search(lead):
        return "fatal"
    if lx.SEVERITY_NONE_RE.search(lead):
        return "no_injury"
    if lx.SEVERITY_INJURY_RE.search(lead):
        return "injury"
    return "unknown"


def road_users(crash_text: str, article_text: str) -> list[str]:
    users = []
    t = crash_text.lower()
    cyc = bool(re.search(r"cyclist|bicycl|e-?bike|\bbike\b|scooter", t))
    ped = "pedestrian" in t or bool(re.search(r"\bwalking\b|\bcrossing\b", t))
    if ped or (not cyc and PERSON_RE.search(t) and not OCCUPANT_RE.search(t)):
        users.append("pedestrian")
    if cyc:
        users.append("cyclist")
    if re.search(r"\bdriver|motorist|operator\b", article_text, re.I):
        users.append("driver")
    if re.search(r"\bttc\b|streetcar|\bbus\b", t, re.I):
        users.append("transit_vehicle")
    return users


def streets(text: str) -> set[str]:
    out = set()
    for m in STREET_RE.finditer(text):
        words = [w for w in m.group(1).split() if w not in STOP_STREET]
        if words:
            out.add(" ".join(words).lower().rstrip("."))
    for m in INTERSECTION_RE.finditer(text):
        for g in m.groups():
            if g.split()[0] not in STOP_STREET:
                out.add(g.lower())
    return out


# French equivalents for French-language outlets (codebook 10.1, D-101).
VRU_WORD_FR_RE = re.compile(
    r"\b(?:piétonne?|cycliste|vélo|bicyclette|trottinette|marcheuse|marcheur|brigadière"
    r"|brigadier)s?\b|\bà pied\b",
    re.I,
)
_PERSON_FR = (
    r"(?:homme|femme|garçon|fille|fillette|enfant|adolescente?|aînée?|personne|dame|jeune"
    r"|élève|octogénaire|septuagénaire|sexagénaire|\d+ ans)s?"
)
_STRIKE_FR = r"(?:happée?s?|heurtée?s?|frappée?s?|percutée?s?|renversée?s?|fauchée?s?)"
STRUCK_PERSON_FR_RE = re.compile(rf"\b{_PERSON_FR}\b[^.;]{{0,80}}?\b{_STRIKE_FR}\b", re.I)
OCCUPANT_FR_RE = re.compile(r"passag[eè]re?s?|occupante?s?|motocycliste|au volant", re.I)
MOTOR_FR_RE = re.compile(
    r"\b(?:conductrice|conducteur|automobiliste|chauffeur|chauffeuse|camionneur|voiture"
    r"|véhicule|auto|automobile|camion|camionnette|fourgonnette|autobus|tramway|taxi|moto"
    r"|motocyclette|vus)s?\b|délit de fuite",
    re.I,
)
FOLLOW_UP_FR_RE = re.compile(
    r"\baccusée?s?\b|\bidentifiée?s?\b|\bvigile\b|\btribunal\b|\bprocès\b|\bcondamnée?\b"
    r"|\bhommage\b|\bcoupable\b|\barrêtée?s?\b|\bfamille de\b|vélo fantôme|\bdeuil\b"
    r"|\bse rend\b",
    re.I,
)
ROUNDUP_FR_RE = re.compile(
    r"(?:deux|plusieurs|trois) (?:collisions|accidents)|(?:collisions|accidents) distincts",
    re.I,
)


def is_crash_article(crash_sents: list[str], title: str, text: str, lang: str = "en") -> bool:
    """In scope (D-01): a crash sentence naming a VRU, and a motor vehicle in the article."""
    if not crash_sents:
        return False
    joined = " ".join(crash_sents)
    if lang == "fr":
        vru = VRU_WORD_FR_RE.search(joined) or (
            STRUCK_PERSON_FR_RE.search(joined) and not OCCUPANT_FR_RE.search(joined)
        )
        return bool(vru and MOTOR_FR_RE.search(f"{title} {text}"))
    vru = VRU_WORD_RE.search(joined) or (
        STRUCK_PERSON_RE.search(joined) and not OCCUPANT_RE.search(joined)
    )
    return bool(vru and MOTOR_RE.search(f"{title} {text}"))


def article_type(title: str, text: str, lang: str = "en") -> str:
    roundup, follow = (
        (ROUNDUP_FR_RE, FOLLOW_UP_FR_RE) if lang == "fr" else (ROUNDUP_RE, FOLLOW_UP_RE)
    )
    if roundup.search(f"{title} {text[:800]}"):
        return "roundup"
    if follow.search(title or ""):
        return "follow_up"
    return "initial"


def _days(a: str, b: str) -> int:
    return abs((date.fromisoformat(a[:10]) - date.fromisoformat(b[:10])).days)


def link_release(art: dict, releases: list[dict]) -> tuple[int | None, float]:
    """Best collision release within the date window, scored by shared streets and VRU type."""
    best, best_score = None, 0.0
    a_streets = art["streets"]
    a_vru = set(art["road_users"]) & {"pedestrian", "cyclist"}
    for r in releases:
        gap = (date.fromisoformat(art["published"]) - date.fromisoformat(r["published"])).days
        if not (-1 <= gap <= 3) and not (art["article_type"] == "follow_up" and 0 <= gap <= 90):
            continue
        shared = len(a_streets & r["streets"])
        vru_match = bool(a_vru & set(r["road_users"]))
        score = shared + (0.5 if vru_match else 0) - 0.1 * max(gap, 0)
        ok = shared >= 2  # D-56: one shared street linked many wrong releases
        if ok and score > best_score:
            best, best_score = r["id"], score
    return best, best_score


def assign_crash_ids(arts: list[dict]) -> None:
    """Group articles about the same crash (codebook 4.7)."""
    arts.sort(key=lambda a: a["published"])
    crashes: list[dict] = []
    for a in arts:
        match = None
        for c in reversed(crashes):
            if a["release_id"] and a["release_id"] == c["release_id"]:
                match = c
                break
            window = 90 if a["article_type"] == "follow_up" else 1
            if _days(a["published"], c["date"]) > window:
                continue
            shared = len(a["streets"] & c["streets"])
            if (shared >= 2 or (shared >= 1 and _days(a["published"], c["date"]) <= 1)) and set(
                a["road_users"]
            ) & set(c["road_users"]) & {"pedestrian", "cyclist"}:
                match = c
                break
        if match is None:
            match = {
                "id": f"c{len(crashes):05d}",
                "date": a["published"],
                "streets": set(a["streets"]),
                "road_users": a["road_users"],
                "release_id": a["release_id"],
            }
            crashes.append(match)
        else:
            match["streets"] |= a["streets"]
            match["release_id"] = match["release_id"] or a["release_id"]
        a["crash_id"] = match["id"]
    # Per outlet, the first article on a crash is initial; later ones are follow-ups (D-17).
    seen: set[tuple[str, str]] = set()
    for a in arts:
        key = (a["outlet"], a["crash_id"])
        if a["article_type"] != "roundup":
            a["article_type"] = "follow_up" if key in seen else a["article_type"]
        seen.add(key)


# Comparison cities (D-100). Same logic as is_toronto: the city's own police or emergency
# service wins; another force, or another municipality in the lead, rules an article out.
CITIES = {
    "vancouver": {
        "own": re.compile(r"vancouver police|\bVPD\b|vancouver fire", re.I),
        "other": re.compile(
            r"\bRCMP\b|surrey police|delta police|abbotsford police|new westminster police"
            r"|port moody police|west vancouver police|victoria police|saanich police",
            re.I,
        ),
        "elsewhere": re.compile(
            r"\b(?:Surrey|Burnaby|Richmond|Coquitlam|North Vancouver|West Vancouver|Delta"
            r"|Langley|Abbotsford|Chilliwack|Maple Ridge|New Westminster|Port Coquitlam"
            r"|Port Moody|Victoria|Kelowna|Kamloops|Nanaimo|Squamish|Whistler|Prince George"
            r"|Saanich|Seattle|Washington state)\b"
        ),
        "name": re.compile(r"(?<!North )(?<!West )\bVancouver\b"),
    },
    "montreal": {
        "own": re.compile(r"montreal police|\bSPVM\b|urgences-sant", re.I),
        "other": re.compile(
            r"s[uû]ret[eé] du qu[eé]bec|\bSQ\b|laval police|longueuil police"
            r"|quebec city police|gatineau police|ottawa police|toronto police",
            re.I,
        ),
        "elsewhere": re.compile(
            r"\b(?:Laval|Longueuil|Quebec City|Gatineau|Sherbrooke|Trois-Rivi\w+|Brossard"
            r"|Terrebonne|Repentigny|Saint-J\w+|Blainville|Mirabel|Boucherville|Vaudreuil"
            r"|Ch[aâ]teauguay|Ottawa|Toronto)\b"
        ),
        "name": re.compile(r"\bMontr[eé]al\b"),
    },
}
CITY_LOCAL = {"citynews", "ctv", "citynews_van", "citynews_mtl", "ctv_van", "ctv_mtl"}


def in_city(city: str, title: str, text: str, local: bool = False) -> bool:
    if city == "toronto":
        return is_toronto(title, text, local)
    c = CITIES[city]
    blob, lead = f"{title}\n{text}", f"{title}\n{text[:400]}"
    if c["own"].search(blob):
        return True
    if c["other"].search(blob) or c["elsewhere"].search(lead):
        return False
    return bool(c["name"].search(blob)) or (local and not WIRE_RE.search(text))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    outlets = config.load()["outlets"]
    releases = []
    for r in con.execute(
        "SELECT id, title, published, text FROM police_releases WHERE is_collision=1"
    ):
        releases.append(
            {
                "id": r["id"],
                "published": r["published"],
                "streets": streets(f"{r['title']}\n{r['text']}"),
                "road_users": road_users(f"{r['title']} {r['text']}", r["text"] or ""),
            }
        )
    arts = []
    for a in con.execute("SELECT * FROM articles WHERE published IS NOT NULL AND published != ''"):
        crash = [
            s["text"]
            for s in con.execute(
                "SELECT text FROM sentences WHERE article_id=? AND is_crash=1", (a["id"],)
            )
        ]
        title, text = a["title"] or "", a["text"] or ""
        city = outlets.get(a["outlet"], {}).get("city", "toronto")
        lang = outlets.get(a["outlet"], {}).get("language", "en")
        # in the comparison databases, is_toronto means "in the outlet's city" (D-100)
        tor = in_city(city, title, text, local=a["outlet"] in LOCAL_OUTLETS | CITY_LOCAL)
        crash_ok = is_crash_article(crash, title, text, lang)
        rec = {
            "id": a["id"],
            "outlet": a["outlet"],
            "published": a["published"],
            "is_toronto": tor,
            "is_crash": crash_ok,
            "severity": severity(title, text),
            "road_users": road_users(" ".join(crash) + " " + title, text),
            "hit_and_run": bool(lx.FLED_RE.search(f"{title} {text}")),
            "article_type": article_type(title, text, lang),
            "streets": streets(f"{title}\n{text[:1500]}"),
            "release_id": None,
            "release_score": None,
        }
        if tor and crash_ok:
            rec["release_id"], rec["release_score"] = link_release(rec, releases)
            arts.append(rec)
        con.execute(
            "UPDATE articles SET is_toronto=?, is_crash=?, severity=?, road_users=?, hit_and_run=?,"
            " article_type=?, release_id=?, release_score=?, crash_id=NULL WHERE id=?",
            (
                int(tor),
                int(crash_ok),
                rec["severity"],
                json.dumps(rec["road_users"]),
                int(rec["hit_and_run"]),
                rec["article_type"],
                rec["release_id"],
                rec["release_score"],
                a["id"],
            ),
        )
    assign_crash_ids(arts)
    for a in arts:
        con.execute(
            "UPDATE articles SET crash_id=?, article_type=? WHERE id=?",
            (a["crash_id"], a["article_type"], a["id"]),
        )
    con.commit()
    n = len(arts)
    linked = sum(1 for a in arts if a["release_id"])
    print(f"in-scope crash articles: {n}; linked to a release: {linked}", flush=True)


if __name__ == "__main__":
    main()
