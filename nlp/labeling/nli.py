"""Zero-shot NLI (deberta-v3-base-zeroshot-v2.0): baseline and labeling function (PLAN.md §8.1).

Each label value is a hypothesis. Scores are cached in SQLite keyed by
(model revision, hypothesis, sentence id), so reruns are free and reproducible.
"""

import argparse

from common import config, db
from nlp.device import get_device

HYPOTHESES: dict[str, list[tuple[str, str]]] = {
    "voice": [
        ("active", "This sentence uses the active voice to say who or what hit someone."),
        ("passive_with_agent", "This sentence is passive and says who or what hit the victim."),
        ("agentless_passive", "This sentence is passive and does not say who hit the victim."),
        ("intransitive", "This sentence says vehicles or people collided, with no one hit."),
        ("nominal", "This sentence mentions a crash or collision without a verb for the impact."),
    ],
    "driver_reference": [
        ("person", "This sentence mentions a person driving."),
        ("vehicle", "This sentence mentions a vehicle but not its driver."),
        ("absent", "This sentence mentions neither a driver nor a vehicle."),
    ],
    "focus": [
        ("vru", "The grammatical subject of this sentence is a pedestrian or cyclist."),
        ("driver", "The grammatical subject of this sentence is a driver."),
        ("vehicle", "The grammatical subject of this sentence is a vehicle."),
        ("other", "The grammatical subject of this sentence is not a road user."),
    ],
    "vru_as_actor": [
        ("true", "The pedestrian or cyclist is described as colliding with something."),
    ],
    "accident_term": [("true", "This sentence calls the crash an accident.")],
    "vru_conduct_detail": [
        (
            "true",
            "This sentence describes what the pedestrian or cyclist was doing, wearing, or "
            "where they were crossing.",
        ),
    ],
    "thematic_cue": [
        (
            "true",
            "This sentence discusses road safety trends, statistics, road design, or policy.",
        ),
    ],
    # v1.5 (codebook 9.1, 9.2)
    "policy_frame": [
        ("economic", "This sentence is about costs, funding, money, or business."),
        ("safety", "This sentence is about safety, injuries, or deaths."),
        ("quality_of_life", "This sentence is about traffic, commute times, or daily life."),
        ("political", "This sentence is about politics, elections, or a government dispute."),
        ("legality", "This sentence is about a law, a court case, or legal rights."),
        (
            "other",
            "This sentence is about how well a service or project is run, its reliability, "
            "oversight, or public opinion.",
        ),
        ("none", "This sentence states a time, place, or event with no policy content."),
    ],
    "stance_infrastructure": [
        (
            "support",
            "This sentence says bike lanes are good, or that someone supports them or opposes "
            "removing them.",
        ),
        (
            "oppose",
            "This sentence says bike lanes are bad, or that someone opposes them or wants them "
            "removed.",
        ),
        ("none", "This sentence states no one's view of bike lanes."),
    ],
    "stance_cyclists": [
        ("positive", "This sentence describes cyclists favourably, or reports someone doing so."),
        ("negative", "This sentence describes cyclists unfavourably, or reports someone doing so."),
        ("none", "This sentence states no one's judgment of cyclists."),
    ],
    "stance_transit": [
        (
            "support",
            "This sentence says a transit project or transit funding is good, or that someone "
            "supports it.",
        ),
        (
            "oppose",
            "This sentence says a transit project or transit funding is bad, or that someone "
            "opposes it.",
        ),
        ("none", "This sentence states no one's view of transit projects or funding."),
    ],
}

CRASH_LABELS = ("voice", "driver_reference", "focus", "vru_as_actor", "accident_term")
CONTEXT_LABELS = ("vru_conduct_detail", "thematic_cue")
V15_LABELS = ("policy_frame", "stance_infrastructure", "stance_cyclists", "stance_transit")
CACHE = """CREATE TABLE IF NOT EXISTS nli_cache (
    revision TEXT, hypothesis TEXT, sentence_id TEXT, score REAL,
    PRIMARY KEY (revision, hypothesis, sentence_id))"""


def decide(label: str, scores: dict[str, float]) -> tuple[str, float]:
    """Categorical: argmax. Binary: 'true' if score >= 0.5 else 'false'."""
    if len(HYPOTHESES[label]) == 1:
        s = scores["true"]
        return ("true" if s >= 0.5 else "false"), s
    best = max(scores, key=scores.get)
    return best, scores[best]


class NLI:
    def __init__(self, con):
        from transformers import pipeline

        m = config.load()["models"]["nli"]
        self.rev = m["revision"]
        self.con = con
        con.execute(CACHE)
        self.pipe = pipeline(
            "zero-shot-classification",
            model=m["name"],
            revision=m["revision"],
            device=get_device(),
        )

    def scores(self, sid: str, text: str, label: str) -> dict[str, float]:
        out = {}
        todo = []
        for value, hyp in HYPOTHESES[label]:
            row = self.con.execute(
                "SELECT score FROM nli_cache WHERE revision=? AND hypothesis=? AND sentence_id=?",
                (self.rev, hyp, sid),
            ).fetchone()
            if row:
                out[value] = row[0]
            else:
                todo.append((value, hyp))
        if todo:
            r = self.pipe(text, [h for _, h in todo], multi_label=True, hypothesis_template="{}")
            by_hyp = dict(zip(r["labels"], r["scores"], strict=True))
            for value, hyp in todo:
                out[value] = float(by_hyp[hyp])
                self.con.execute(
                    "INSERT OR REPLACE INTO nli_cache VALUES (?,?,?,?)",
                    (self.rev, hyp, sid, out[value]),
                )
        return out


def run(con, rows: list[tuple[str, str, tuple[str, ...]]]) -> None:
    """rows: (sentence_id, text, labels). Writes labels with source 'nli'."""
    nli = NLI(con)
    for n, (sid, text, labels) in enumerate(rows):
        for label in labels:
            value, score = decide(label, nli.scores(sid, text, label))
            con.execute(
                "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
                (sid, label, "nli", value, score, "zero-shot NLI"),
            )
        if n % 200 == 0:
            con.commit()
            print(f"nli {n}/{len(rows)}", flush=True)
    con.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--ids", help="file with sentence ids, one per line (default: eval + pools)")
    args = ap.parse_args()
    con = db.connect(args.db)
    ids = [ln.strip() for ln in open(args.ids)] if args.ids else None
    q = "SELECT id, text, is_crash FROM sentences"
    rows = []
    for r in con.execute(q):
        if ids is not None and r["id"] not in ids:
            continue
        labels = CRASH_LABELS if r["is_crash"] else ()
        rows.append((r["id"], r["text"], labels + CONTEXT_LABELS))
    run(con, rows)


if __name__ == "__main__":
    main()
