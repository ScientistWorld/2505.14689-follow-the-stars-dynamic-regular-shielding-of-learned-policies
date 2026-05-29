#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

cd /home/user

STEPS="${STEPS:-20000}"

python method/factorybot_method.py \
  --steps "$STEPS" \
  --output checkpoints/factorybot_results.jsonl

bash scripts/evaluate.sh checkpoints/factorybot_results.jsonl
