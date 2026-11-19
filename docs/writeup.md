# How Toronto news frames crashes involving pedestrians and cyclists

<!-- Results are filled in after the full pipeline run (PROGRESS.md). Sections marked TODO. -->

## Coverage

In-scope crash articles per outlet per quarter (`analysis/tables/coverage_by_quarter.csv`). Coverage is uneven: CTV's sitemaps start in 2025, and three outlets remain after exclusions (see Limitations). Outlet comparisons use only the window all three cover; trends are reported within each outlet; before/after Bill 212 uses only outlets with articles on both sides.

TODO: coverage table.

## Key results

TODO.

Pooled tables (text source, headline vs body, fatal vs non-fatal, initial vs follow-up, exceptional vs ordinary driver, article-level rates) combine all outlets over the full window. Each is shown next to its per-outlet breakdown (`*_by_outlet.csv`). For each one, state which outlet contributes most of the pooled sample (`pooled_sample_shares.csv`), since a pooled rate leans toward that outlet's rate. The breakdowns decompose the pooled sample; they are not outlet comparisons, which use the common window (D-45).

TODO: per pooled table, largest contributor and its share.

## Methods

See `docs/method.md` for the full method. Points that affect how to read the results:

- **Test labels came from an LLM annotator** (a Claude Code subagent given only the codebook and the raw sentences), not a human. A second LLM annotator labeled 30 test sentences for Cohen's kappa. Accuracy figures therefore measure agreement with an LLM reading of the codebook.
- **Police releases from the Wayback Machine.** The Toronto Police site blocks scripted access, so releases come from Wayback Machine copies. They are public government records, not commercial content, and the project publishes no release text beyond short excerpts. Wayback copies of blogTO and Toronto Today were not used: those are commercial outlets whose live sites block scripted access, and using archive copies would get around that choice. About 42% of releases in the window are archived, so the police comparison covers a matched subset and is checked against unmatched articles.
- Grammatical labels come from dependency rules; two fuzzy labels come from a SetFit model trained on Snorkel labels. Rates have 95% bootstrap intervals over articles.

## Evaluation

TODO.

## Comparison with prior studies

TODO (docs/related-work.md).

## Limitations

- **Dropped outlets.** Four planned outlets are not in the corpus:
  - Toronto Sun: Postmedia's terms ban scraping (D-19).
  - blogTO and Toronto Today: both block scripted access; their Wayback copies were not used (D-20, D-46).
  - CBC: its robots.txt could not be reached from the collection network, which is treated as no permission (D-33).

  Dropping the Toronto Sun removes the main right-leaning outlet in the planned set. The remaining outlets (CityNews, CTV, Global) are mainstream broadcasters' news sites, so outlet comparisons cover a narrower range of editorial positions than planned and cannot speak to differences across the political spectrum.
- **Uneven coverage.** CTV covers 2025 onward only, and Global is national (a Toronto filter selects local crashes).
- **LLM-annotated test set.** See Methods.

TODO: remaining limitations after results.
