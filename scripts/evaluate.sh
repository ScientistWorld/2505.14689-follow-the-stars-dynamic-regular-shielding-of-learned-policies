#!/bin/bash
# Score every runtime guide on disk against the visible FactoryBot suite.
#
# A method is a guide spec checkpoints/guides/<name>.json:
#   {"name": "...", "module": "path/to/guide.py", "factory": "make_guide", "params": {...}}
# The scorer (eval/train/, self-contained, never imports method/) builds the
# guide for every grid and reward budget, runs it for 100,000 steps against
# its own simulator, nominal policy and random numbers, and computes every
# metric itself. The unshielded and naive baselines are always scored by the
# evaluator. Output: scoring/scores.json.
#
# Usage: bash scripts/evaluate.sh            (no arguments)
#        GUIDES_DIR=some/dir bash scripts/evaluate.sh   (development only)

set -e

cd /home/user

mkdir -p scoring

python eval/train/factorybot_eval_train.py \
  --guides-dir "${GUIDES_DIR:-checkpoints/guides}" \
  --output scoring/scores.json
