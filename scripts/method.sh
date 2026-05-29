#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

STEPS="${STEPS:-100000}"
SUITE="${SUITE:-data/factorybot_suite.json}"
REGENERATE_SUITE="${REGENERATE_SUITE:-0}"

EXTRA_ARGS=()
if [ "$REGENERATE_SUITE" = "1" ]; then
  EXTRA_ARGS+=(--regenerate-suite)
fi

python method/factorybot_method.py \
  --suite "$SUITE" \
  --steps "$STEPS" \
  --output checkpoints/factorybot_results.jsonl \
  "${EXTRA_ARGS[@]}"

bash scripts/evaluate.sh checkpoints/factorybot_results.jsonl
