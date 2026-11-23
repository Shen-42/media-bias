# Project site: design brief

The project site (`site/`, published on GitHub Pages) explains the findings and how to use the browser extension. It follows `DESIGN.md` (kept outside the repo) and the vocabulary in `design-vocabulary.md`.

## Problem

- **Content:** rates of grammatical forms in Toronto crash coverage, with intervals; comparisons by text source, headline, article type, outlet and city; v1.5 stance results; the evaluation and its main caveat (LLM-annotated test labels); install steps for the extension.
- **Audience:** reporters and editors, road safety advocates, and researchers. Some will disagree with the author, so the page has to be neutral and show its evidence.
- **What the page must help them do:** understand what "the driver is not named" means in grammatical terms, see how often each form occurs and how sure the estimate is, see where the wording comes from, know what the results do not show, and install the extension.

## Compositions considered

- **Report with stat tiles:** a large headline number, cards for each finding, charts below. Rejected: tiles drop the intervals, and the layout could carry any project.
- **Interactive explorer:** filters by outlet, year and text source over every table. Rejected: the findings are a handful of comparisons, most of which show no difference. Filters would invite readers to hunt for differences the intervals do not support.
- **Sentence first (chosen):** the page opens with one crash written in the five voice forms from the codebook, each beside its share of newsroom sentences. Later figures reuse the same row anatomy (label, bar or dot with interval, value). This puts the project's unit of analysis, the sentence, at the top of the hierarchy, and teaches the vocabulary the rest of the page uses.

## Decisions

- Prose in a serif text face (Source Serif 4), codebook labels and numbers in a monospace face (IBM Plex Mono), matching the extension's label tags.
- Single reading column; figures are slightly wider than the text.
- Color encodes text source only: newsroom in the first categorical slot (blue), police-matched in the second (orange), from the validated dataviz palette. Other comparisons use filled and hollow markers in ink.
- Every mark has a native tooltip and every figure has a table view.
- Example sentences are the constructed examples from `codebook.md`, labeled as constructed.
- Numbers are generated from `analysis/tables/` by `site/build.py`, so the page cannot drift from the tables.

## Review (2026-11-23)

A critic subagent, given only the vocabulary, the criteria, the screenshots and the page source, reviewed two rounds.

- **Round 1** found a false claim: the page, the write-up and the summary said every outlet interval overlapped, but 5 of 72 comparisons do not (D-103). Corrected everywhere; the build now asserts the set of non-overlapping pairs. Other changes: stance plotted as support and oppose with intervals, focus caveat in the captions that plot focus, coverage check moved to the methods section, kappa described as self-consistency, phone fixes.
- **Round 2** found denominator mismatches in the bike lane section and a lede claim resting on unvalidated stance labels. The per-outlet figure was replaced by counts that sum to the stated 7 of 511, the stance caveat moved next to the claims, the lede now says the sample is LLM-annotated, and zero rates use a rule-of-three upper bound.
- **Defended:** one "Comparisons" section (each part compares the same measures across a different split); the light-only popup screenshot (it shows a separate product); accuracy without an interval (macro-F1 carries it).

