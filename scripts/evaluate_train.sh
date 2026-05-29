#!/bin/bash
# Visible train-slice evaluation for FactoryBot method artifacts.
#
# Mirrors scripts/evaluate.sh: pass the JSONL method artifact as the first
# optional argument. Writes scoring/scores_train.json.

set -e

cd /home/user

mkdir -p scoring

INPUT="${1:-checkpoints/factorybot_results.jsonl}"
REWARD_GAP_BUDGET="${REWARD_GAP_BUDGET:-0.4}"

python eval/train/factorybot_eval_train.py \
  --input "$INPUT" \
  --output scoring/scores_train.json \
  --reward-gap-budget "$REWARD_GAP_BUDGET"
