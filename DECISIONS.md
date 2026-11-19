# Decisions

Judgment calls made in autonomous mode. Each entry gives the date, the decision, the alternatives, and the reason. Codebook entries (D-01 to D-17) are referenced from `codebook.md`.

## Codebook (2026-11-19)

| ID | Decision | Alternatives | Reason |
|---|---|---|---|
| D-01 | In scope: a motor vehicle (including motorcycles, buses, streetcars) struck a pedestrian or cyclist. A cyclist striking a pedestrian is out. Wheelchair and mobility-device users count as pedestrians; e-bike and e-scooter riders count as cyclists; motorcyclists are not VRUs. | Include cyclist–pedestrian crashes; treat micromobility as its own group | Q10 names motor vehicles as striking vehicles. Ontario law treats mobility-device users as pedestrians. Too few micromobility crashes for a separate group. |
| D-02 | Impact verbs extended to: hit, strike, run over, collide, crash (into), knock down, mow down, pin, drag, clip, door, back into, plow into, slam into, ram. | Keep the four-verb list | Four verbs miss common crash wording; the filter would drop real crash sentences. |
| D-03 | "accident" is a collision noun. | Score `accident_term` on all sentences | Without it, "The accident happened at…" never reaches `accident_term`, which would undercount the label the guidelines care most about. |
| D-04 | "A cyclist died" alone is not a crash sentence; "died after the crash" is. | Add death verbs to the filter | Keeps the filter tied to the collision itself, as defined in Q11. |
| D-05 | Impact verb present → label by its form; no impact verb but a collision noun → `nominal`; `intransitive` = impact verb with no struck road user as object (incl. "X and Y collided"). First impact clause wins. | `intransitive` for any intransitive main verb (e.g. "died") | Removes the overlap between `intransitive` and `nominal` and makes the label computable from the parse. |
| D-06 | `driver_reference = vehicle` when a vehicle appears in the impact clause as agent or other party; "the TTC" counts as vehicle. | Vehicle only as agent | "Collided with a car" still describes the crash through the vehicle, not the driver, which is the framing the label measures. |
| D-07 | `focus` for a conjoined subject = first conjunct. | New value `mixed` | Keeps the codebook's four values; first conjunct is what a reader sees as the subject. |
| D-08 | "A cyclist and a car collided" → `vru_as_actor = yes`. "Stepped into the path" → `vru_conduct_detail`, not actor. | The reverse | The sentence presents the VRU as a co-agent; movement without an impact verb is conduct, not grammatical agency. |
| D-09 | `accident_term`: lemma "accident" only; not "accidentally", "incident", "mishap". | Wider softener lexicon | Matches the Road Collision Reporting Guidelines focus and prior studies' "accident" counts. |
| D-10 | `vru_conduct_detail` is scored on every VRU-mentioning sentence in a crash article (`vru_sentence`), counts details in either direction, and rolls up to `vru_conduct_any`. | Crash sentences only; fault-implying details only | Conduct details usually sit in their own sentence; restricting to crash sentences would miss most of them. Counting both directions avoids judging fault. |
| D-11 | `text_source = quoted` only for direct speech whose impact clause (or most of the sentence) is inside quotation marks. Indirect speech goes through release matching; a boolean `attributed` records attribution. | Indirect speech counts as quoted | Otherwise most crash sentences ("police say…") would be `quoted` and the police-matching comparison would be empty. |
| D-12 | `driver_exceptional`: fled, impaired, Criminal Code charge, street racing/stunt driving. HTA charges recorded separately (`driver_hta_charge`), not exceptional. Speeding or suspended licence alone: not exceptional. | Any charge counts | HTA tickets are routine in Toronto releases; counting them would make ordinary cases "exceptional" and blur the Fevyer & Aldred "rogue driver" split. |
| D-13 | `thematic_frame` from sentence-level `thematic_cue`; a speaker counts only when referring to a cause, pattern, or fix beyond this crash. | Count any politician or advocate quote | Condolences are episodic; the label is about systemic framing. |
| D-14 | `police_overlap` denominator = non-quoted body sentences; null without a linked release. | All sentences; zero without a release | Quotes cannot be police-matched by definition (precedence); null avoids mixing "no release" with "no overlap". |
| D-15 | `severity` stored for both article and crash; crash keeps the worst outcome. | One of the two | Follow-ups often report a death later; both views are needed. |
| D-16 | `road_users`: transit vehicle adds `driver` only if an operator is mentioned. | Always add `driver` | Matches the text, not an inference. |
| D-17 | `article_type = initial` per outlet; label by fetched content; store fetch time. | First article across all outlets | Per-outlet comparisons need each outlet's own first report. |
| D-18 | Codebook examples stay synthetic. | Replace with real Toronto sentences | Keeps article text out of the repo and out of Qwen prompts, and removes any chance of test leakage. `eval/excluded_ids.txt` still exists and is enforced. |

## Sources and data (2026-11-19)

| ID | Decision | Alternatives | Reason |
|---|---|---|---|
| D-19 | Toronto Sun excluded. | Collect anyway | Postmedia terms: "Web Scraping shall not be permitted under any circumstance without the prior consent of Postmedia." CLAUDE.md requires respecting outlet terms. |
| D-20 | blogTO and Toronto Today excluded. Their Wayback copies are not used either. | Fetch through the Wayback Machine | Both return 403 (Toronto Today: Cloudflare challenge) to a scripted client. Using an archive to reach a site that blocks scripted access would get around its bot protection. TPS is different: the author directed Wayback use for police releases. |
| D-21 | CityNews, CTV, Global included. | Exclude all outlets with "personal, non-commercial use" terms | Rogers, Bell Media and Corus terms limit use to personal, non-commercial use and forbid redistribution; none has an explicit scraping ban. This project is non-commercial research, keeps text local, and publishes only aggregates and short excerpts. Fetches respect robots.txt and crawl-delay (CityNews asks for 10 s). |
| D-22 | CBC: retry during collection; exclude if still unreachable. | Exclude now | robots.txt timed out from this network on 2026-11-18 and 2026-11-19. |
| D-23 | URL discovery uses outlet sitemaps. CTV sitemaps only exist from about 2025, so CTV covers a shorter window; per-outlet windows are reported. | GDELT for older CTV | The GDELT DOC API only searches recent months; its raw files are too large to scan from this network. |
| D-24 | Committed eval CSVs hold sentence IDs and labels, not sentence text. Text is joined from `data/` at run time. | Commit text | The repo is pushed to GitHub; CLAUDE.md allows labels with sentence IDs and short excerpts only. |

## Environment and models (2026-11-19)

| ID | Decision | Alternatives | Reason |
|---|---|---|---|
| D-25 | Pin `transformers<5`; coreference uses the default `FCoref` model. | Patch fastcoref; LingMess | fastcoref 2.1.6 fails on transformers 5.x (`all_tied_weights_keys`). LingMess fails on 4.57 too (Longformer has no SDPA attention). FCoref works on CPU and MPS. |
| D-26 | `vru_conduct_detail` and `thematic_cue` evaluation uses a second sample of body sentences from crash articles (`set = context`), alongside the crash-sentence sample (`set = crash`). | Evaluate on crash sentences only | Both labels mostly occur outside crash sentences (D-10, D-13). |
| D-27 | The Streamlit app is not deployed; it runs locally in "public" mode (aggregates + one excerpt per article) and "local" mode (full viewer). | Deploy to Streamlit Cloud | Hosting needs an account; the author ruled out services needing a human action. |
| D-28 | `da-roberta-babe-ft` not used in v1. | Add as a feature | PLAN.md lists it as a v1.5 stance baseline only. |
