# Related work: prior studies, labels, and rates

Status: partly verified. Ralph et al. (2019) was checked against the paper on 2026-11-20. Fevyer & Aldred (2022) could not be read (open copy returned HTTP 403). Other numbers come from PLAN.md and have not been checked; a "?" in the Verified column means it still needs checking. Blank cells mean unknown. Do not fill a rate without a page or table reference.

The last column says how each study compares with this project, as CLAUDE.md requires. Fill the label columns while reading each paper, and map each label to the codebook dimension it matches (focus, agency, voice, language, narrative framing).

## Crash coverage: content analyses and experiments

| Study | Country | Sample | Unit | Labels used | Rates reported | Verified | Relation to this project |
|---|---|---|---|---|---|---|---|
| Ralph, Iacobucci, Thigpen & Goddard (2019), TRR 2673(2) | US | 200 local news articles (100 pedestrian, 100 cyclist), Feb–Mar 2018, hand-coded (p. 665) | Sentence (focus, agency, object-based language, sentence types); article (counterfactuals, thematic framing, crash term) | Focus, agency (voice), object-based language (driver_reference), counterfactuals (vru_conduct_detail), thematic framing, "accident" | One-third of crash sentences had no agent; in agentive sentences the VRU was the focus 74%; object-based language 81% when a driver or vehicle was mentioned; driver absent from the article 27% (p. 667). "A VRU was hit by a car" 40% of body sentences, 29% of titles (p. 667). Counterfactuals in one-third of articles; thematic elements in 16% (p. 668). "Accident" 47% of body sentences, 11% of titles (p. 669). | Yes (2026-11-20, author PDF) | Same dimensions, coded by hand on a two-month US sample. This project codes a full Toronto corpus with rules over 2023–2026 and adds the police release comparison. Agent and object-based rates are close to this project's; "accident" is far rarer here (docs/writeup.md). |
| Goddard, Ralph, Thigpen & Iacobucci (2019) | US | 999 readers (experiment) | Reader response | Manipulated: pedestrian- vs. driver-focused language; episodic vs. thematic framing | | ? | Tests effects on readers. This project does not test effects; it measures how often the tested patterns occur. |
| German replication of Goddard et al. | Germany | | | | | ? | Citation still needed. |
| Fevyer & Aldred (2022), *Mobilities* | UK (London, *Evening Standard*, 2012–2019) | | | Driver reference (person vs. vehicle); exceptional ("rogue") drivers | | ? | One outlet. Source of `driver_exceptional`. This project compares several outlets. |
| "Framing systemic traffic violence: Media coverage of Dutch traffic crashes" (University of Amsterdam; authors to verify) | Netherlands | 368 local reports | | | | ? | Includes non-fatal crashes and all vehicle types; source of the non-fatal decision. This project limits scope to crashes involving a pedestrian or cyclist. |
| Reymond & Rérat, *Findings* | Switzerland | 204 articles, 2020–2024 | | Five dimensions: focus, agency, voice, language, narrative framing | | ? | Same five-dimension structure. Did not assess police influence; this project does. |
| Von Schneidemesser et al. (2025), *Mobilities* | Germany, Austria, Switzerland | | | Passive voice, metonymy, reflexive verbs | | ? | Reflexive verbs have no English equivalent; passive and metonymy map to `voice` and `driver_reference`. |
| Parachute (2020), Vision Zero media audit | Canada | | | Vision Zero policy coverage | | ? | Closest Canadian precedent. Covers policy coverage, not sentence-level crash framing. |

## Police press releases

| Study | Country | Sample | Unit | Labels used | Rates reported | Verified | Relation to this project |
|---|---|---|---|---|---|---|---|
| Ralph, Goddard, Thigpen & Davis (2022), "Intervening at the blotter, not the broadcast" | US | | | | Journalists draw heavily from police releases (qualitative claim in PLAN.md) | ? | Studies releases on their own. This project links each article to its release. |
| Laker (2024), Foundation for Integrated Transport | UK | 227 police releases | Release | "Accident" use; vehicles described as autonomous agents | 70% describe vehicles as autonomous agents; "accident" rare | ? | Releases only. Gives a reference rate for `driver_reference = vehicle` in police text. |

## Automated tools

| Study | Country | Sample | Unit | Labels used | Rates reported | Verified | Relation to this project |
|---|---|---|---|---|---|---|---|
| Zhao et al. (2025), "Bike Frames", ICWSM | US | 31,480 headlines; 1,500 annotated | Headline | Accident detection, fault, cyclist perception | | ? | Headlines only, hosted LLM, US. Not used as an evaluation set here (different unit, labels, country). Reports that outlet information improves prediction. |
| Vision Zero Reporting (Lang, 2021) | | | Article | Six problems based on Ralph et al.; letter grade | | ? | Method and code not public. This project shows per-sentence evidence, not grades. |

## Quotes, frames, and bias (supporting methods)

| Study | Country | Sample | Unit | Labels used | Rates reported | Verified | Relation to this project |
|---|---|---|---|---|---|---|---|
| Asr et al. (2021), Gender Gap Tracker, *PLoS ONE* | Canada | Seven English outlets | Quote | Quote and speaker extraction | | ? | Reused for quote stripping and source counts. |
| Rissel et al. (2010) | Australia (Sydney, Melbourne) | | Article | Cycling vs. cyclists framing | Cycling coverage more positive than negative; cyclist coverage more negative (direction only) | ? | v1.5. Source of the cycling vs. cyclists split. |
| Card et al. (2015), Media Frames Corpus; Boydstun et al., Policy Frames Codebook | US | | | 15 policy frames | | ? | v1.5 frames. |
| Spinde et al. (2021), BABE | | 3,700 expert-labeled sentences | Sentence | Media bias (loaded language) | | ? | Feature only. Trained on US political news. This project rejects its outlet-based distant labels. |
| Horych et al. (2025), Anno-lexical, NAACL Findings | | 48k LLM-labeled sentences | Sentence | Lexical bias | Trained classifier beat each annotator LLM by 5–9% | ? | Uses a local model (Qwen) as one Snorkel input, not the only labeler. |

## Reporting guidelines (suggestions, not labels)

| Source | Country | Use here |
|---|---|---|
| Road Collision Reporting Guidelines (Laker & Active Travel Academy, 2021) | UK | Edge-case reference for the codebook; rewrite suggestions, labeled as suggestions |
| Ralph et al., Guide to Improving Police Press Releases About Car Crashes (Rutgers) | US | Same |
