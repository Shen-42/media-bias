#!/usr/bin/env bash
# v1.5 steps after run_pipeline.sh (which splits sentences, applies the Toronto filter and
# text_source to every article). Annotation happens between --sample and the final run.
set -euo pipefail
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=${PY:-.venv/bin/python}
step() { echo "== $*"; caffeinate -i "$PY" -m "$@"; }

if [[ "${1:-}" == "--sample" ]]; then
  step nlp.v15 --steps topics sources pools
  step eval.sample_v15 sentences            # once; then annotate test/dev packets
  step nlp.v15 --steps nli qwen
  step nlp.v15 --steps snorkel setfit
  step eval.sample_v15 disagreement
  step nlp.v15 --steps nli qwen             # new disagreement rows (cached otherwise)
  step nlp.v15 --steps babe
  echo "Annotate data/eval/in/packet_*v15*.jsonl, then run ./run_v15.sh"
  exit 0
fi
step nlp.v15 --steps snorkel setfit
step eval.score_v15
step analysis.aggregate_v15
