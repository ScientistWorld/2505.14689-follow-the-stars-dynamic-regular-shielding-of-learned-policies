#!/bin/bash
# Held-out test-slice evaluation for FactoryBot method artifacts.
#
# Mirrors scripts/evaluate.sh: pass the JSONL method artifact as the first
# optional argument. Writes scoring/scores_test.json.

set -e

cd /home/user

mkdir -p scoring

INPUT="${1:-checkpoints/factorybot_results.jsonl}"
REWARD_GAP_BUDGET="${REWARD_GAP_BUDGET:-0.4}"
TRAIN_SCORES="${TRAIN_SCORES:-scoring/scores_train.json}"

python eval/test/factorybot_eval_test.py \
  --input "$INPUT" \
  --output scoring/scores_test.json \
  --train-scores "$TRAIN_SCORES" \
  --reward-gap-budget "$REWARD_GAP_BUDGET"
