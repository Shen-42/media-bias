"""Split articles into sentences, find crash sentences, apply rules, mark quotes.

Headline and body are stored separately (part = headline | body). Only regex candidates are
parsed with the transformer model; the small model does sentence splitting.
"""

import argparse
import re

import spacy

from common import config, db
from nlp import quotes, rules
from nlp.lexicons import VRU_CONTEXT

CANDIDATE_RE = re.compile(
    r"\b(?:hit|hits|struck|strikes?|striking|collid\w*|crash\w*|pinn?\w*|dragg?\w*|clipp\w*"
    r"|door(?:ed|ing)|ramm?\w*|run(?:s|ning)? over|ran over|knock\w* (?:down|over)|mow\w* down"
    r"|back\w* into|plow\w* into|plough\w* into|slamm?\w* into|smash\w* into|accident\w*"
    r"|collision\w*|hit-and-run)\b",
    re.I,
)
VRU_RE = re.compile(r"\b(?:pedestrian|cyclist|bicyclist|e-?biker|scooter rider|jogger)s?\b", re.I)

RULE_LABELS = ("voice", "driver_reference", "focus", "vru_as_actor", "accident_term")


def load_models():
    cfg = config.load()["models"]["spacy"]
    return spacy.load(cfg["fast"]), spacy.load(cfg["parser"])


BOILERPLATE_RE = re.compile(
    r"^(?:Posted|Last Updated|Updated|Published)\b.*\d{4}.*$|^By [A-Z][^.]{0,60}$|^Share$", re.I
)


def clean_body(title: str | None, text: str | None) -> str:
    """Drop a repeated headline and dateline/byline lines that trafilatura keeps."""
    lines = []
    for ln in (text or "").split("\n"):
        s = ln.strip()
        if not s or BOILERPLATE_RE.match(s) or (title and s == title.strip()):
            continue
        lines.append(s)
    return "\n".join(lines)


def split(nlp_sm, title: str | None, text: str | None) -> list[dict]:
    out = []
    if title:
        out.append({"part": "headline", "idx": 0, "text": title.strip(), "start": 0, "end": 0})
    if text:
        # Split each paragraph separately so no sentence crosses a line break.
        i, offset = 0, 0
        for para in text.split("\n"):
            if para.strip():
                for s in nlp_sm(para).sents:
                    t = s.text.strip()
                    if len(t) < 3:
                        continue
                    out.append(
                        {
                            "part": "body",
                            "idx": i,
                            "text": t,
                            "start": offset + s.start_char,
                            "end": offset + s.end_char,
                        }
                    )
                    i += 1
            offset += len(para) + 1
    return out


def process_article(con, nlp_sm, nlp_trf, art) -> int:
    body = clean_body(art["title"], art["text"])
    sents = split(nlp_sm, art["title"], body)
    body_spans = quotes.quote_spans(body)
    title_spans = quotes.quote_spans(art["title"] or "")
    cand = [s for s in sents if CANDIDATE_RE.search(s["text"])]
    parsed = {id(s): d for s, d in zip(cand, nlp_trf.pipe([s["text"] for s in cand]), strict=True)}
    for s in sents:
        sid = f"{art['id']}:{'h' if s['part'] == 'headline' else 'b'}:{s['idx']}"
        spans = title_spans if s["part"] == "headline" else body_spans
        start, end = (0, len(s["text"])) if s["part"] == "headline" else (s["start"], s["end"])
        is_crash, impact_range = False, None
        doc = parsed.get(id(s))
        if doc is not None:
            sent = doc[:]
            is_crash, why = rules.is_crash_sentence(sent)
            if is_crash:
                imp = rules.find_impact(sent)
                if imp.verb is not None:
                    a, b = imp.tokens[0].idx, imp.tokens[-1].idx + len(imp.tokens[-1])
                    impact_range = (start + a, start + b)
                for name, (val, ev) in rules.label_crash_sentence(sent).items():
                    con.execute(
                        "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
                        (sid, name, "rule", str(val).lower(), None, ev),
                    )
        quoted = quotes.is_quoted(start, end, spans, impact_range)
        is_vru = bool(VRU_RE.search(s["text"]) or (is_crash and VRU_CONTEXT.search(s["text"])))
        con.execute(
            "INSERT OR REPLACE INTO sentences (id, article_id, part, idx, text, is_crash, is_vru,"
            " quoted, attributed) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                sid,
                art["id"],
                s["part"],
                s["idx"],
                s["text"],
                int(is_crash),
                int(is_vru),
                int(quoted),
                int(quotes.is_attributed(s["text"])),
            ),
        )
    return len(sents)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--redo", action="store_true", help="drop all sentences and labels first")
    args = ap.parse_args()
    con = db.connect(args.db)
    if args.redo:
        con.execute("DELETE FROM labels")
        con.execute("DELETE FROM sentences")
        con.commit()
    nlp_sm, nlp_trf = load_models()
    arts = con.execute(
        "SELECT a.* FROM articles a WHERE NOT EXISTS"
        " (SELECT 1 FROM sentences s WHERE s.article_id = a.id) ORDER BY published"
    ).fetchall()[: args.limit]
    for n, art in enumerate(arts):
        process_article(con, nlp_sm, nlp_trf, art)
        con.commit()
        if n % 100 == 0:
            print(f"sentences {n}/{len(arts)}", flush=True)
    print(f"sentences done: {len(arts)} articles", flush=True)


if __name__ == "__main__":
    main()
