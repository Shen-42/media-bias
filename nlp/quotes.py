"""Direct-quote spans and attribution (codebook §3.1, D-11, D-29).

Quote spans are found per paragraph. News style repeats the opening quote mark on each
paragraph of a multi-paragraph quote, so an unclosed quote runs to the end of its paragraph.
"""

import re

OPEN = {"“": "”", '"': '"', "«": "»"}
ATTRIB_RE = re.compile(
    r"\b(?:said|says|say|told|tells|stated|states|reported|reports|alleged|alleges|confirmed"
    r"|confirms|added|adds|noted|explained|wrote|claimed|believe[sd]?)\b|according to",
    re.I,
)


def quote_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    pos = 0
    for para in text.split("\n"):
        i = 0
        while i < len(para):
            ch = para[i]
            if ch in OPEN:
                close = OPEN[ch]
                j = para.find(close, i + 1)
                end = len(para) if j == -1 else j + 1
                spans.append((pos + i, pos + end))
                i = end
            else:
                i += 1
        pos += len(para) + 1
    return spans


def inside_share(start: int, end: int, spans: list[tuple[int, int]]) -> float:
    if end <= start:
        return 0.0
    covered = sum(max(0, min(end, b) - max(start, a)) for a, b in spans)
    return covered / (end - start)


def is_quoted(
    start: int,
    end: int,
    spans: list[tuple[int, int]],
    impact: tuple[int, int] | None = None,
) -> bool:
    """D-11: impact clause inside quotes (crash sentences) or most of the sentence (others)."""
    if impact is not None:
        return inside_share(impact[0], impact[1], spans) > 0.5
    return inside_share(start, end, spans) > 0.5


def is_attributed(sentence: str) -> bool:
    return bool(ATTRIB_RE.search(sentence))
