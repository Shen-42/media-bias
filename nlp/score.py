"""Score one article's text with the rule-based labeler (used by the browser extension, D-102).

Returns each crash sentence with its labels, the evidence for each label, whether it is
quoted, and rewrite suggestions for non-quoted sentences. Nothing is stored. There is no
article score or grade (CLAUDE.md presentation rules).
"""

from nlp import quotes, rewrite, rules, rules_fr
from nlp.sentences import CANDIDATE_RE, clean_body, split


def score_article(nlp_sm, nlp_trf, title: str, text: str, lang: str = "en") -> list[dict]:
    R, cand = (rules_fr, rules_fr.CANDIDATE_RE) if lang == "fr" else (rules, CANDIDATE_RE)
    body = clean_body(title, text)
    spans = {"headline": quotes.quote_spans(title or ""), "body": quotes.quote_spans(body)}
    out = []
    for s in split(nlp_sm, title, body):
        if not cand.search(s["text"]):
            continue
        sent = nlp_trf(s["text"])[:]
        ok, why = R.is_crash_sentence(sent)
        if not ok:
            continue
        start, end = (0, len(s["text"])) if s["part"] == "headline" else (s["start"], s["end"])
        quoted = quotes.is_quoted(start, end, spans[s["part"]])
        labels = {k: [str(v).lower(), ev] for k, (v, ev) in R.label_crash_sentence(sent).items()}
        out.append(
            {
                "part": s["part"],
                "text": s["text"],
                "why": why,
                "quoted": quoted,
                "labels": labels,
                # rewrites are English-only and never offered for a source's own words
                "suggestions": [] if quoted or lang != "en" else rewrite.suggest(sent),
            }
        )
    return out
