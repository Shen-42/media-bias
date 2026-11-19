# Progress

Autonomous run of Phases 0–3. Updated after each task. A new session resumes from "Next".

## Done
- Phase 0: plan decisions recorded (PLAN.md §3); CLAUDE.md autonomous-mode rules; repo skeleton; device detection.
- Phase 0: TPS archive check (Wayback, 42% of IDs in window); dependency spike (transformers<5, FCoref).
- Phase 0: codebook v1.0 with all flags resolved (D-01..D-18); docs/sources.md; docs/licenses.md; config/config.toml with model pins; lockfile.

- GitHub private repo Shen-42/media-bias with Actions (ruff + pytest) — passing.
- Collectors: sitemap discovery, polite fetcher, Wayback police releases, dedupe, crash metadata/linking.
- NLP: sentence split + crash filter, dependency rules (template suite: 312/312 on trf and sm), quotes, overlap/text_source, coref.
- Labeling: NLI runner, Qwen labeler (schema, cache), LFs, Snorkel, SetFit helpers.

## Running in background (detached; logs in data/logs/)
- `collect.police` (Wayback, ~11 h), `collect.discover` for citynews/ctv/global, `collect.fetch citynews` (~6 h tier 1).

## Next
1. Fetch CTV and Global once discovery finishes: `python -m collect.fetch ctv` / `global`.
2. Eval sampler + excluded_ids test; nlp.labeling.run orchestration; pipeline run on partial corpus.
3. Phase 1: discovery (sitemaps), fetch/extract, police releases (Wayback), dedupe, crash metadata, linking, corpus stats.
4. Phase 2: sentence filter, quotes, rules, coref, overlap, LFs, NLI, Qwen, Snorkel, SetFit, eval sets via annotator subagents, scoring.
5. Phase 3: analysis tables with bootstrap CIs, Streamlit app, write-up, SUMMARY.md.

## Blockers
- None. Watch: `qwen3:4b` pull in progress; CBC unreachable so far.
