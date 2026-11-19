#!/usr/bin/env bash
# Full pipeline after collection. Each step caches its outputs in data/corpus.sqlite.
# Collection (hours, rate-limited) runs separately:
#   python -m collect.discover {citynews,ctv,global}; python -m collect.fetch {outlet}
#   python -m collect.police
set -euo pipefail
PY=${PY:-.venv/bin/python}
step() { echo "== $*"; caffeinate -i "$PY" -m "$@"; }

step nlp.sentences --redo   # split, crash filter, rules, quotes (rebuilds all)
step collect.crash          # Toronto/crash filter, metadata, release + crash linking
step collect.dedupe         # wire groups
step nlp.overlap            # release similarity -> text_source
step nlp.coref              # driver mentions, VRU sentences
if [[ "${1:-}" == "--eval-sample" ]]; then
  step eval.sample random   # test/dev random rows (once; then annotate)
fi
step nlp.labeling.run --steps pools nli qwen
if [[ "${1:-}" == "--eval-sample" ]]; then
  step eval.sample disagreement
  step nlp.labeling.run --steps nli qwen   # new disagreement rows (cached otherwise)
  echo "Annotate data/eval/packet_*.jsonl, then rerun without --eval-sample."
  exit 0
fi
step eval.tune              # text_source thresholds from dev only
step nlp.labeling.run --steps snorkel setfit
step nlp.article
step eval.score
step analysis.aggregate
