# Licenses of models, data, and reused code

Checked 2026-11-19 from Hugging Face model cards and installed package metadata.

## Models

| Model | Revision | License | Used in v1 |
|---|---|---|---|
| spaCy `en_core_web_trf` | 3.8.0 | MIT | Yes: parsing for grammatical rules |
| spaCy `en_core_web_sm` | 3.8.0 | MIT | Yes: fast tests and CI |
| `biu-nlp/f-coref` (fastcoref FCoref) | e91dfff12879495d882ba9460d0c5d5dd44ade59 | MIT | Yes: coreference |
| `biu-nlp/lingmess-coref` | fa5d8a827a09388d03adbe9e800c7d8c509c3935 | MIT | No: fails on current transformers (D-25) |
| `MoritzLaurer/deberta-v3-base-zeroshot-v2.0` | 8e7e5af5983a0ddb1a5b45a38b129ab69e2258e8 | MIT | Yes: zero-shot baseline and labeling function |
| `sentence-transformers/all-mpnet-base-v2` | e8c3b32edf5434bc2275fc9bab85f82640a19130 | Apache-2.0 | Yes: release matching |
| `sentence-transformers/all-MiniLM-L6-v2` | 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 | Apache-2.0 | Yes: SetFit base |
| Qwen3 4B (`qwen3:4b` via Ollama) | digest pinned in `config/config.toml` | Apache-2.0 | Yes: one labeling function |
| `mediabiasgroup/da-roberta-babe-ft` | a1e1b9e2ac97f87387fb0b78e5a1914b5e25532f | CC-BY-NC-4.0 | No (v1.5 only). Non-commercial license; fine for this project, but note it if the code is reused commercially |

## Libraries

| Package | Version | License |
|---|---|---|
| spaCy | 3.8.18 | MIT |
| fastcoref | 2.1.6 | MIT |
| Snorkel | 0.10.0 | Apache-2.0 |
| SetFit | 1.2.0 | Apache-2.0 |
| trafilatura | 2.3.1 | Apache-2.0 |
| datasketch | 2.0.0 | MIT |

## Reused code

The Gender Gap Tracker quote extractor is not used. Quote detection uses the spaCy + regex fallback (PLAN.md 8.3), so its license does not apply.

## Data

- Article text: copyright of each outlet. Stored locally in `data/`, never committed or published (CLAUDE.md).
- Toronto Police news releases: fetched from the Internet Archive's Wayback Machine. Stored locally; only IDs, match scores, and short excerpts are published.
