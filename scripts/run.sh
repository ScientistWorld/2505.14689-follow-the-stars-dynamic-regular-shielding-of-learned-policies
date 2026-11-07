#!/bin/bash
# Job script: reproduce the reference end to end, then run the
# iteration-11 hardening audit (variants and shortcuts through the hidden test).

set -e

cd /home/user
export PYTHONDONTWRITEBYTECODE=1
mkdir -p tmp

bash scripts/download.sh
python method/factorybot_method.py
if [ ! -f tmp/.done_ref_train ]; then
  bash scripts/evaluate_train.sh
  cp scoring/scores_train.json scoring/scores.json
  touch tmp/.done_ref_train
fi
if [ ! -f tmp/.done_ref_test ]; then
  bash scripts/evaluate_test.sh
  touch tmp/.done_ref_test
fi
bash redteam/hardening/run_hardening.sh
