#!/bin/bash
# Hardening audit (iteration 11). Run as a CPU job after the reference
# pipeline has produced checkpoints/guides/apply_stars.json and the clean
# scoring/scores_{train,test}.json. Every step is resumable via done-markers.
set -euo pipefail
cd /home/user

OUT=redteam/hardening/out
ROWS=tmp/hardening_rows
SPECS=tmp/hardening_specs
mkdir -p "$OUT" "$ROWS"

step() {
  local name=$1
  shift
  if [ -f "$OUT/.done_$name" ]; then
    echo "[hardening] skip $name (done)"
    return
  fi
  echo "[hardening] start $name $(date -u +%H:%M:%S)"
  "$@"
  touch "$OUT/.done_$name"
  echo "[hardening] done $name $(date -u +%H:%M:%S)"
}

python redteam/hardening/build_specs.py

step test_variants python eval/test/factorybot_eval_test.py \
  --guides-dir "$SPECS/test" --output "$OUT/test_variants.json" --rows-out "$ROWS/test_variants.jsonl"
step tamper bash redteam/hardening/tamper.sh
python redteam/hardening/summarize.py
step noise_alt1 python eval/test/factorybot_eval_test.py \
  --guides-dir "$SPECS/ref_only" --rng-salt alt1 --output "$OUT/test_noise_alt1.json"
step train_variants python eval/train/factorybot_eval_train.py \
  --guides-dir "$SPECS/train" --output "$OUT/train_variants.json" --rows-out "$ROWS/train_variants.jsonl"
python redteam/hardening/summarize.py
step noise_alt2 python eval/test/factorybot_eval_test.py \
  --guides-dir "$SPECS/ref_only" --rng-salt alt2 --output "$OUT/test_noise_alt2.json"
python redteam/hardening/summarize.py
