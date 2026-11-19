# Media Bias & Framing Detector

This project measures how Toronto local news frames traffic crashes involving pedestrians and cyclists, and reports the results by outlet and over time. The first version asks one question: how often do Toronto outlets describe crashes in ways that hide the driver, and how much of that language comes from Toronto Police news releases rather than the newsroom? The tool measures framing. It does not start from a conclusion about any outlet or government.

Results and limitations are in [`docs/writeup.md`](docs/writeup.md). Labels are defined in [`codebook.md`](codebook.md). Judgment calls are logged in [`DECISIONS.md`](DECISIONS.md).

## Important: how the test labels were made

The test and dev labels used to evaluate this pipeline were produced by an **LLM annotator** (a Claude Code subagent given only the codebook and the raw sentences), **not by a human**. A second, independent LLM annotator labeled 30 test sentences to estimate agreement. This limits what the evaluation can show:

- Accuracy figures measure agreement with an LLM reading of the codebook, not with expert human judgment.
- Two LLM annotators may share blind spots, so their agreement (Cohen's kappa) can overstate how clear the codebook is.
- An LLM annotator can be biased toward the same surface cues that the rules and the Qwen labeling function use.

The pipeline itself uses no LLM APIs. Its only LLM is Qwen3 4B, run locally through Ollama as one weak labeling function among several.

## What it does

1. Discovers crash articles in outlet sitemaps (CityNews Toronto, CTV News Toronto, Global News) and fetches them politely (robots.txt, ≥ 2 s per domain, CityNews 10 s). The Toronto Sun, blogTO, Toronto Today and CBC were excluded for terms, bot blocking, or an unreachable robots.txt (`docs/sources.md`).
2. Collects Toronto Police news releases from the Wayback Machine and links articles to them.
3. Labels each crash sentence with dependency rules: grammatical voice, how the driver is referred to, the grammatical subject, whether the pedestrian or cyclist is presented as an actor, and use of "accident". Each label carries its evidence.
4. Labels two fuzzier properties (pedestrian/cyclist conduct details, thematic framing) with a SetFit model trained on Snorkel labels from lexicons, zero-shot NLI and Qwen.
5. Marks each sentence as quoted, police-matched, or newsroom text, and reports rates for each separately.
6. Reports rates with bootstrap confidence intervals, never rankings or letter grades.

## Setup

```
python3.11 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_trf && python -m spacy download en_core_web_sm
ollama pull qwen3:4b
```

Runs on CPU or Apple Silicon (MPS); CUDA is optional. Tested on an 8 GB M2.

## Run

```
python -m collect.discover citynews     # also: ctv, global
python -m collect.fetch citynews        # rate-limited; hours
python -m collect.police                # Wayback Machine; hours
./run_pipeline.sh --eval-sample         # first time: builds eval packets for annotation
./run_pipeline.sh                       # labels, tuning (dev only), scoring, analysis
streamlit run app/streamlit_app.py      # MEDIA_BIAS_MODE=local adds the full-text viewer
pytest && ruff check .
```

## Data and copyright

Article text and HTML stay in `data/` and are never committed. The repo publishes code, labels keyed by sentence ID, aggregate tables, and at most one short excerpt per article for examples. The public dashboard mode shows only those; the full-text viewer runs locally.
