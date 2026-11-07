#!/bin/bash
# Hidden test scoring of every guide spec in checkpoints/guides/.
#
# eval/test/ generates the held-out FactoryBot grids and rollout seeds,
# computes the nominal policy and both baselines itself, runs every guide
# through the runtime-guide interface, and writes scoring/scores_test.json.
# Takes no arguments. Nothing a method wrote (rollout rows, metrics, score
# files) is read.

set -e

cd /home/user

mkdir -p scoring

python eval/test/factorybot_eval_test.py --output scoring/scores_test.json
