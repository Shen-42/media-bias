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

## Running in background (detached; logs in data/logs/)
- `collect.police` (Wayback, ~11 h).
- `collect.fetch citynews` (tier 1 then tier 2, 10 s/article).
- `collect.discover ctv` / `global`; a watcher starts `collect.fetch ctv` / `global` when each finishes.

## Next
1. When collection finishes: `./run_pipeline.sh --eval-sample`.
2. Annotator subagents on data/eval/packet_*.jsonl (codebook.md + sentences only) → eval/dev_crash.csv, eval/test_crash.csv, eval/test_crash_annotator2.csv (30 rows).
3. `./run_pipeline.sh` (tune on dev, Snorkel, SetFit, article labels, scoring, aggregates).
4. Write docs/writeup.md with results, compare with docs/related-work.md; SUMMARY.md with top 10 decisions.

## Blockers
- None. CTV sitemaps only cover ~2025 onward (shorter window for CTV).
