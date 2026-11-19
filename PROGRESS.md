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

## Running in background (detached; logs in data/logs/). Times are CST.
| Job | State at 2026-11-20 05:30 | ETA |
|---|---|---|
| `./run_pipeline.sh --eval-sample` (log: pipeline_eval_sample.log) | sentences for 2,373 new CityNews articles, then crash filter, dedupe, overlap, coref, eval sampling, NLI and Qwen on pools | 2026-11-20 ~11:30 |

Collection finished 2026-11-20 05:00 with no failed fetches. Crash-topic articles: CityNews 4,063, Global 4,818, CTV 1,449. 16 CTV daily sitemaps return 504 on every try; 14 predate CTV's first article (D-51).

## Next
1. Annotator subagents (~1 h, ~12:30): codebook.md + packets only → eval/dev_crash.csv, eval/test_crash.csv, eval/test_crash_annotator2.csv (30 rows).
2. `./run_pipeline.sh` (~1 h, ~13:30): tune on dev, Snorkel, SetFit, article labels, scoring, aggregates.
3. Fill docs/writeup.md TODOs and write SUMMARY.md (~1.5 h, ~15:00).

## Blockers
- None.
