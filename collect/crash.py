"""Article metadata, crash linking and police-release linking (PLAN.md §6 steps 4, 5, 7).

Runs after nlp.sentences (it needs crash sentences). All rules are lexical and explainable.
"""

import argparse
import json
import re
from datetime import date

from common import db
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
VRU_WORD_RE = re.compile(r"\b(pedestrian|cyclist|bicyclist|e-?bike|bike|bicycle|scooter)s?\b", re.I)
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


def is_toronto(title: str, text: str) -> bool:
    blob = f"{title}\n{text}"
    if OTHER_POLICE_RE.search(blob) and not TORONTO_POLICE_RE.search(blob):
        return False
    if TORONTO_POLICE_RE.search(blob):
        return True
    lead = f"{title}\n{text[:400]}"
    return "Toronto" in blob and not OTHER_CITY_RE.search(lead)


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
    if "pedestrian" in t or re.search(r"\bwalking\b|\bcrossing\b", t):
        users.append("pedestrian")
    if re.search(r"cyclist|bicycl|e-?bike|\bbike\b|scooter", t):
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


def is_crash_article(crash_sents: list[str], title: str, text: str) -> bool:
    """In scope (D-01): a crash sentence naming a VRU, and a motor vehicle in the article."""
    if not crash_sents:
        return False
    joined = " ".join(crash_sents)
    return bool(VRU_WORD_RE.search(joined) and MOTOR_RE.search(f"{title} {text}"))


def article_type(title: str, text: str) -> str:
    if ROUNDUP_RE.search(f"{title} {text[:800]}"):
        return "roundup"
    if FOLLOW_UP_RE.search(title or ""):
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
        ok = shared >= 2 or (shared >= 1 and vru_match and abs(gap) <= 1)
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
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
        tor = is_toronto(title, text)
        crash_ok = is_crash_article(crash, title, text)
        rec = {
            "id": a["id"],
            "outlet": a["outlet"],
            "published": a["published"],
            "is_toronto": tor,
            "is_crash": crash_ok,
            "severity": severity(title, text),
            "road_users": road_users(" ".join(crash) + " " + title, text),
            "hit_and_run": bool(lx.FLED_RE.search(f"{title} {text}")),
            "article_type": article_type(title, text),
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
