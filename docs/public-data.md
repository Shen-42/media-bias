# Public data that could check or extend this project

Researched 2026-11-22. Every label in this project comes from LLM annotators, so the main use of outside data is human-labeled checks. None of these sets is a drop-in substitute for human labels on this corpus: they use other text, topics or label schemes. They can show whether a component works on human-labeled data. Licences and download links were not all confirmed, as noted below.

## Human-labeled text (validation of components)

| Dataset | What it has | Use here | Fit | Status |
|---|---|---|---|---|
| Media Frames Corpus (Card et al. 2015) | Human frame annotations on US news about immigration, tobacco, same-sex marriage and other issues, using the Boydstun policy frames | Check the `policy_frame` systems (NLI, Qwen) against human labels on the same frame scheme | Same frames as codebook 9.1; different topics and country | Annotations on GitHub (`dallascard/media_frames_corpus`); article text needs a LexisNexis licence |
| SemEval-2023 Task 3, subtask 2 | Article-level frame labels (14 Boydstun frames) in English and five other languages | A second frame check | Article level, not sentence level | Released through the task organizers; download terms not confirmed |
| BABE (Spinde et al. 2021) | About 3,700 sentences with expert sentence- and word-level bias labels | Validate the BABE loaded-language score on held-out expert labels before reporting it (now unreported) | US political news, not local transport | Public; the model already in use was trained on it, so only its test split is a fair check |
| MBIC | About 1,700 crowd-labeled sentences | Weak extra check for loaded language | Crowd labels, kappa 0.21 | Public |
| PolNeAR | Attribution relations in political news | Already used for quote stripping; could also score the `attributed` rule (D-91) | Close: news attribution | Already in PLAN.md |
| PARC 3.0 | About 20,000 attribution relations | Another attribution check | Many attributions unannotated (PolNeAR found most missing) | "Available for research use"; download not confirmed |
| SEESAW (EMNLP 2022) | Sentence-level entity-to-entity stance in 609 news articles | Closest English sentence-level stance set | Targets are people and topics, not transport policy | Paper public; data link not checked |
| Bike Frames (Zhao et al., ICWSM 2025) | 31,480 US headlines about cyclists, 1,500 human annotations | Human-labeled check of how cyclists are portrayed in headlines; compare with `stance_cyclists` and v1 headline labels | Headlines only, US | Paper says CC BY 4.0 via Zenodo; record not confirmed |

No public English dataset was found with sentence-level stance toward transport policy. The labels closest to this project's core measures (stance on bike lanes and transit, crash-sentence grammar) would need a human-labeled sample of this corpus.

Published crash-coverage studies (Ralph et al. 2019; Goddard et al. 2019; the Hillsborough County, Florida study of 190 reports; Scheffels-style discourse studies) report coded rates but did not release item-level data in the sources found. Their rates are already the comparison points in `docs/related-work.md`.

## Toronto records (ground truth for coverage, not for labels)

| Dataset | What it has | Use here |
|---|---|---|
| Toronto Police Public Safety Data Portal: Killed or Seriously Injured (KSI) collisions | Every collision with a death or serious injury, with pedestrian and cyclist fields | Which crashes get covered and how (PLAN.md nice-to-have); check v1 `severity` and `road_users` against police records for matched crashes. Recent months lag by 6 months or more |
| City of Toronto Open Data: Cycling Network | Bikeways with type and installation year | Link bike-lane coverage to specific installations and removals (Bloor, Yonge, University) |
| City of Toronto Vision Zero dashboard and annual reports | Deaths and serious injuries by year and mode | Context for how coverage volume tracks harm |
| TTC and Metrolinx open data (ridership, service) | Service levels | Context for transit coverage; not a label check |

The City notes a recent problem transferring KSI data to its Vision Zero dashboard and points to the TPS portal instead. A York University study found police data undercounts pedestrian and cyclist injuries, so KSI is a floor.

## Recommendation

1. Score the frame systems on the Media Frames Corpus annotations. Not done (D-97): the repo is deprecated and the article text needs LexisNexis Academic access through an account. SemEval-2023 Task 3, the other news set with this frame scheme, needs a registration form. If you have library access to LexisNexis, this can be revisited.
2. Score the `attributed` rule on PolNeAR. Done 2026-11-22 (D-94): precision 0.90, recall 0.49 against PolNeAR's broader attribution definition (`eval/polnear_check.py`).
3. Link v1 crash articles to the KSI records. Done 2026-11-22 (D-95, `analysis/ksi_link.py`): 26% of pedestrian and cyclist KSI crashes got an initial report; `road_users` agreed with police on 98% of linked reports, `severity` on 90%. The data came from the City of Toronto Open Data portal (Open Government Licence - Toronto), not the TPS portal.
5. BABE test split: done (D-96, `eval/babe_check.py`): macro-F1 0.82, an upper bound because the model may have trained on it.
4. For stance and crash grammar there is no public substitute. A small human-labeled sample of this corpus (about 50 sentences per label) remains the only direct check of the LLM annotator.

## Sources

- Media Frames Corpus: https://aclanthology.org/P15-2072/ ; data https://github.com/dallascard/media_frames_corpus
- SemEval-2023 Task 3 overview: https://aclanthology.org/2023.semeval-1.317
- BABE: https://arxiv.org/abs/2209.14557 ; MBIC and BABE comparison: https://aclanthology.org/2021.findings-emnlp.101
- PARC 3.0: https://aclanthology.org/L16-1619/ ; PolNeAR: https://www.cs.mcgill.ca/~enewel3/pdfs/polnear.pdf
- SEESAW: https://aclanthology.org/2022.emnlp-main.676.pdf
- Bike Frames: https://arxiv.org/abs/2301.06178 ; https://ojs.aaai.org/index.php/ICWSM/article/view/35934
- Gender Gap Tracker (Canadian quote extraction, code only): https://github.com/sfu-discourse-lab/GenderGapTracker
- TPS data portal and KSI: https://www.tps.ca/data-maps/data-analytics/fatal-collisions/ ; https://mdl.library.utoronto.ca/node/48251
- City of Toronto cycling network: https://www.toronto.ca/services-payments/streets-parking-transportation/cycling-in-toronto/torontos-cycling-infrastructure
- Vision Zero dashboard: https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-dashboard/
- Police undercount study (CBC): https://www.cbc.ca/1.7084128
