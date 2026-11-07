#!/bin/bash
# Run the paper's proposed method (ApplySTARs) end to end.
#
# 1. method/factorybot_method.py sweeps the enforcement parameter gamma over
#    the paper's grid on the visible suite (100,000 steps per grid), picks
#    one global gamma per reward budget, and writes the guide spec
#    checkpoints/guides/apply_stars.json (resumable sweep cache in
#    checkpoints/stars_sweep.jsonl).
# 2. scripts/evaluate.sh scores the guide on the visible suite.

set -e

cd /home/user

python method/factorybot_method.py "$@"

bash scripts/evaluate.sh
