# Progress

Autonomous run of Phases 0–3. Updated after each task. A new session resumes from "Next".

## Done
- Phase 0: plan decisions (PLAN.md §3); CLAUDE.md autonomous rules; skeleton; device detection; TPS archive check; dependency spike; codebook v1.0 (D-01..D-18); sources, licenses, config pins, lockfile; GitHub repo with CI.
- Phase 1 code: sitemap discovery with fetch tiers (D-32, D-38), polite fetcher, Wayback police releases, crash metadata and linking (D-39, D-40), dedupe (D-34).
- Phase 2 code: sentence split and crash filter, dependency rules (template suite 312/312), quotes, overlap/text_source, coref, NLI, Qwen labeler, LFs, Snorkel fit/predict, SetFit, labeling orchestrator, eval sampler with excluded_ids test, triage, scoring (P/R/F1, macro-F1, bootstrap CI, kappa), dev-only threshold tuning, article labels.
- Phase 3 code: analysis/aggregate.py (cluster bootstrap CIs; text_source, headline/body, outlet with/without wire, year, fatal, initial/follow-up, exceptional driver split, matched-vs-unmatched check, corpus stats, excerpts); Streamlit app (public/local modes); README with LLM-annotator disclosure; docs/method.md; run_pipeline.sh.
- Dry run of every pipeline step on the partial corpus succeeded. Qwen (digest pinned, ~3 s/sentence) and NLI (MPS, ~0.5 s/pair) smoke-tested.
- UD EWT passive component check: clausal participles P 0.92 / R 0.80 / F1 0.85 (D-41). PolNeAR skipped (no license, D-42).
- Annotator instructions (eval/annotation/instructions.md) and merge tool (eval/merge_labels.py).
- Coverage rules (D-45): outlet comparisons in the common window, per-outlet trends, Bill 212 pre/post (cutoff 2024-11-25, D-47) only for outlets on both sides, coverage-by-quarter table. Wayback distinction logged (D-46). docs/writeup.md skeleton with coverage, methods and limitations sections.
- Police releases complete (2026-11-19 19:54, retry pass done): 5,336 of 5,347 archived IDs; 5,219 in window; 334 collision releases; 11 unrecoverable 404s (D-49).
- Pooled tables each have a per-outlet breakdown and outlet sample shares with the largest contributor flagged (D-48); shown in the dashboard; app handles empty tables (headless smoke test passes).

## Outlets
- Collected: CityNews Toronto, CTV News Toronto (sitemaps start 2025; 2023-24 daily sitemaps are empty), Global News (national; Toronto filter applies).
- Dropped: Toronto Sun (Postmedia terms ban scraping, D-19); blogTO and Toronto Today (403 / Cloudflare to scripted clients; Wayback copies not used either, D-20); CBC (robots.txt unreachable from this network, last retried 2026-11-19, D-22/D-33).

## Collection resilience (D-43)
- Every per-item result is committed to SQLite, so a killed or slept process resumes from where it stopped on restart.
- Article fetch: failures stored as `failed:*` per URL and printed to the log; `--retry-failed` requeues them (not blocks or 404s). Police: non-ok IDs are retried automatically on rerun.
- Fetcher waits out network outages (up to 2 h) instead of failing a run of URLs. Discovery skips and logs failed sitemaps, records finished ones, and treats non-200 as failed.
- Jobs started before this change (police, CityNews fetch, CTV discovery) run old code; the retry pass in Next step 1 covers them. Failures so far: 0.

## Phase 3 run (finished 2026-11-20)
- Rescope after annotator findings (D-54, D-56, D-58): 942 in-scope articles, 3,114 crash sentences, 218 release-linked.
- Eval: dev 100 rows and test 240 rows (160 random + 80 disagreement) labeled by claude-subagent; out-of-scope rows replaced (D-55); second annotator 30 rows (kappa 1.0 on 26 crash rows).
- Pipeline: tune (dev macro-F1 0.915, thresholds embed 0.6 / char 0.2), Snorkel, SetFit, article labels, scoring, aggregates. Offline model loading (D-59).
- docs/writeup.md filled; docs/related-work.md has verified Ralph et al. (2019) rates; SUMMARY.md written.
- CLAUDE.md untracked and removed from git history (D-57).

## Phase 4 (v1.5), started 2026-11-20
Done:
- Model choice: Snorkel + SetFit for stance and frames (author, D-60). CLAUDE.md updated.
- Codebook Part B draft (sections 7–9): topic, source_role, policy_frame, three stance targets, loaded_language feature (D-63); label mapping in docs/related-work.md.
- Bill 212 timeline with sources (`analysis/timeline_bill212.csv`, D-64).
- Fetch fix for non-crash topics (D-62); broader bike lane slugs and `--rescan` (D-61); topic tagger `nlp/topic.py` (D-65).

Running (logs in data/logs/):
| Job | Log | Then |
|---|---|---|
| Fetch bike_lane then transit URLs, per outlet | fetch_v15_<outlet>.log (prints FETCH_DONE) | rescan sitemaps with the broader slugs, fetch new bike_lane URLs (rescan_<outlet>.log, prints RESCAN_DONE) |

Next:
1. Source extraction: speaker + role rules for `source_role` (codebook 8.1), with tests.
2. Labeling functions for `policy_frame` and the stance targets: lexicons, NLI hypotheses, Qwen prompt v1.5 (examples from codebook only).
3. After fetching: sentences, Toronto filter, topic tags, text_source on v1.5 articles.
4. v1.5 eval sample (dev and test, random + disagreement, plus a topic-precision sample); annotator subagents.
5. Snorkel + SetFit; aggregates by outlet, text_source and Bill 212 period; dashboard view; write-up addendum.

## v1 follow-ups (not started)
1. Trace why Global's in-scope count drops after mid-2024.
2. Revise the codebook for the gaps the annotators found (charge names with "accident", bare person nouns, general statements, emergency vehicles, sentence-level VRU scope), then relabel.
3. Rework the fuzzy-label models on dev only; SetFit and Snorkel trailed single labeling functions on test.

## Blockers
- None.
