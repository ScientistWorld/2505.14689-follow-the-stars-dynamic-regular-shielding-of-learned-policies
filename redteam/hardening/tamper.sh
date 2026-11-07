#!/bin/bash
# Plant all file-level shortcuts, run the hidden test with no arguments,
# keep its output, and restore every touched file.
set -euo pipefail
cd /home/user

OUT=redteam/hardening/out
BK=tmp/tamper_backup
rm -rf "$BK"
mkdir -p "$BK" "$OUT"
cp scoring/scores_test.json scoring/scores_train.json data/factorybot_nominal.py "$BK/"
cp -r checkpoints/guides "$BK/guides"
HAD_ARTIFACT=0
if [ -f checkpoints/factorybot_results.jsonl ]; then
  cp checkpoints/factorybot_results.jsonl "$BK/"
  HAD_ARTIFACT=1
fi

restore() {
  cp "$BK/scores_test.json" "$BK/scores_train.json" scoring/
  cp "$BK/factorybot_nominal.py" data/
  rm -rf checkpoints/guides
  cp -r "$BK/guides" checkpoints/guides
  if [ "$HAD_ARTIFACT" = "1" ]; then
    cp "$BK/factorybot_results.jsonl" checkpoints/
  else
    rm -f checkpoints/factorybot_results.jsonl
  fi
  echo "[tamper] restored original files"
}
trap restore EXIT

python redteam/hardening/tamper_files.py
bash scripts/evaluate_test.sh
cp scoring/scores_test.json "$OUT/tamper_scores_test.json"
