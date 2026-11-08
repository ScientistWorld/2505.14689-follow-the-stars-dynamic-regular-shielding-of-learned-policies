#!/bin/bash
# Job script: reproduce the reference end to end (CPU only).
#
# 1. Tune ApplySTARs on the visible suite and write checkpoints/guides/apply_stars.json.
# 2. Score every guide on disk on the visible suite (train) and on the hidden test.
#
# The iteration-11 hardening audit (variants and shortcuts) can be rerun with
#   bash redteam/hardening/run_hardening.sh
# after these steps.

set -e

cd /home/user
export PYTHONDONTWRITEBYTECODE=1

bash scripts/download.sh
python method/factorybot_method.py
bash scripts/evaluate_train.sh
cp scoring/scores_train.json scoring/scores.json
bash scripts/evaluate_test.sh
