"""Agreement-based triage (PLAN.md §9.5). Agreement is not accuracy; this only picks rows."""

from collections import defaultdict

from nlp.lexicons import CONDUCT_RE, THEMATIC_RE

CRASH = ("voice", "driver_reference", "focus", "vru_as_actor", "accident_term")
CONTEXT = {"vru_conduct_detail": CONDUCT_RE, "thematic_cue": THEMATIC_RE}


def count(votes: dict[str, dict[str, str | None]]) -> int:
    """Number of labels on which the non-abstaining sources disagree."""
    n = 0
    for by_source in votes.values():
        vals = {v for v in by_source.values() if v is not None}
        n += len(vals) > 1
    return n


def disagreement_counts(con) -> dict[tuple[str, str], int]:
    votes: dict[str, dict[str, dict[str, str | None]]] = defaultdict(lambda: defaultdict(dict))
    for r in con.execute(
        "SELECT sentence_id, label, source, value FROM labels WHERE source IN ('rule','nli','qwen')"
    ):
        votes[r["sentence_id"]][r["label"]][r["source"]] = r["value"]
    for r in con.execute("SELECT id, text FROM sentences"):
        if r["id"] in votes:
            for label, rx in CONTEXT.items():
                if label in votes[r["id"]]:
                    votes[r["id"]][label]["lexicon"] = "true" if rx.search(r["text"]) else "false"
    out = {}
    for sid, by_label in votes.items():
        out[(sid, "crash")] = count({k: v for k, v in by_label.items() if k in CRASH})
        out[(sid, "context")] = count({k: v for k, v in by_label.items() if k in CONTEXT})
    return out
