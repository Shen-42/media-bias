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
The Mac rebooted at ~11:47 on 2026-11-20 and stopped the eval-sample run at Qwen 200/1,590 (D-52).
Annotators then flagged out-of-scope articles: US wire stories on CityNews Toronto pages, car-only crashes, and wrong police-release links. Fixed in D-54 (scope) and D-56 (release links); in-scope crash articles drop from 1,671 to about 940.
| Job | State at 2026-11-20 12:40 | ETA |
|---|---|---|
| crash → dedupe → overlap → coref on the new scope (log: rescope.log, prints SCOPE_DONE) | running | ~13:15 |

## Eval labels
- Annotated and merged (claude-subagent): dev 100 rows; test random 160 rows; second annotator 30 test crash rows (`eval/test_crash_annotator2.csv`).
- These rows predate the rescope. `eval.sample topup` drops rows now out of scope and adds random replacements (D-55).

## Next
1. After SCOPE_DONE: `python -m eval.sample topup`; annotate the topup packets (`data/eval/packet_topup_*`); merge.
2. `python -m nlp.labeling.run --steps pools nli qwen` (pools rebuilt on new scope; Qwen cache reused), then `eval.sample disagreement`, `--steps nli qwen`, annotate the disagreement rows.
3. `./run_pipeline.sh` (no flag): tune on dev, Snorkel, SetFit, article labels, scoring, aggregates.
4. Fill docs/writeup.md TODOs and write SUMMARY.md.

## Blockers
- None.
