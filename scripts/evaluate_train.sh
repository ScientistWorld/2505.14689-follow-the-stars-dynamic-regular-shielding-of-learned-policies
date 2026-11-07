#!/bin/bash
# Visible train-slice scoring of every guide spec in checkpoints/guides/.
#
# Runs each guide on the visible 383-grid FactoryBot suite (visible rollout
# seeds) through eval/train/ and writes scoring/scores_train.json. Takes no
# arguments; GUIDES_DIR may point at another spec directory during
# development.

set -e

cd /home/user

mkdir -p scoring

python eval/train/factorybot_eval_train.py \
  --guides-dir "${GUIDES_DIR:-checkpoints/guides}" \
  --output scoring/scores_train.json
