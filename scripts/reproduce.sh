#!/bin/bash
# Reproduce the reference results end to end (CPU only, ~2-3 CPU-hours).
#
# Assumes the container is built and scripts/download.sh has been run.

set -e

cd /home/user

bash scripts/download.sh
python method/factorybot_method.py
bash scripts/evaluate_train.sh
cp scoring/scores_train.json scoring/scores.json
bash scripts/evaluate_test.sh
