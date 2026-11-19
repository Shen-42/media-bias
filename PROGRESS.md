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

## Outlets
- Collected: CityNews Toronto, CTV News Toronto (sitemaps start 2025; 2023-24 daily sitemaps are empty), Global News (national; Toronto filter applies).
- Dropped: Toronto Sun (Postmedia terms ban scraping, D-19); blogTO and Toronto Today (403 / Cloudflare to scripted clients; Wayback copies not used either, D-20); CBC (robots.txt unreachable from this network, last retried 2026-11-19, D-22/D-33).

## Collection resilience (D-43)
- Every per-item result is committed to SQLite, so a killed or slept process resumes from where it stopped on restart.
- Article fetch: failures stored as `failed:*` per URL and printed to the log; `--retry-failed` requeues them (not blocks or 404s). Police: non-ok IDs are retried automatically on rerun.
- Fetcher waits out network outages (up to 2 h) instead of failing a run of URLs. Discovery skips and logs failed sitemaps, records finished ones, and treats non-200 as failed.
- Jobs started before this change (police, CityNews fetch, CTV discovery) run old code; the retry pass in Next step 1 covers them. Failures so far: 0.

## Running in background (detached; logs in data/logs/). Times are CST.
| Job | State at 2026-11-19 15:35 | Rate | ETA |
|---|---|---|---|
| `collect.police` (Wayback) | 1,284 of ~5,400 IDs | 2.3 s/ID | 2026-11-19 ~18:15 |
| `collect.fetch citynews` | 1,217 tier 1 + 2,602 tier 2 left | ~16 s/URL (10 s crawl delay + latency) | tier 1 ~21:00; all 2026-11-20 ~08:30 |
| `collect.fetch global` | 2,258 tier 1 + 4,638 tier 2 left | ~2.5 s/URL | 2026-11-19 ~20:30 |
| `collect.discover ctv` → rediscover (retry 504 days) → `collect.fetch ctv` | discovery at 2024-12 | ~2 min/month | discovery ~16:45, rediscovery ~18:00, fetch done ~19:00 |

## Next (ETAs assume collection ends 2026-11-20 ~08:30 CST)
1. Retry pass (~30 min, ~09:00): `python -m collect.police`; `python -m collect.fetch {citynews,global,ctv} --retry-failed`; rerun `collect.discover` for any outlet whose log shows FAILED.
2. `./run_pipeline.sh --eval-sample` (~7 h, ~16:00): sentences + trf parse, crash filter, dedupe, overlap, coref, NLI and Qwen on pools (Qwen ~3 s/sentence is most of it).
3. Annotator subagents (~1 h, ~17:00): codebook.md + packets only → eval/dev_crash.csv, eval/test_crash.csv, eval/test_crash_annotator2.csv (30 rows).
4. `./run_pipeline.sh` (~1 h, ~18:00): tune on dev, Snorkel, SetFit, article labels, scoring, aggregates.
5. docs/writeup.md, comparison with docs/related-work.md, SUMMARY.md (~1.5 h, ~19:30).

## Blockers
- None.
