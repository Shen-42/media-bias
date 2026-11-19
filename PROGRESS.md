# Progress

Autonomous run of Phases 0–3. Updated after each task. A new session resumes from "Next".

## Done
- Phase 0: plan decisions recorded (PLAN.md §3); CLAUDE.md autonomous-mode rules; repo skeleton; device detection.
- Phase 0: TPS archive check (Wayback, 42% of IDs in window); dependency spike (transformers<5, FCoref).
- Phase 0: codebook v1.0 with all flags resolved (D-01..D-18); docs/sources.md; docs/licenses.md; config/config.toml with model pins; lockfile.

## Next
1. GitHub private repo + Actions (ruff, pytest).
2. Phase 0: excluded_ids + sampler test; template suite seed; skeleton pipeline on 5 articles.
3. Phase 1: discovery (sitemaps), fetch/extract, police releases (Wayback), dedupe, crash metadata, linking, corpus stats.
4. Phase 2: sentence filter, quotes, rules, coref, overlap, LFs, NLI, Qwen, Snorkel, SetFit, eval sets via annotator subagents, scoring.
5. Phase 3: analysis tables with bootstrap CIs, Streamlit app, write-up, SUMMARY.md.

## Blockers
- None. Watch: `qwen3:4b` pull in progress; CBC unreachable so far.
