#!/bin/bash
# Example job script submitted via the end-of-turn YAML block.
#
# This runs inside the compute container with:
#   - Your workspace mounted at /home/user
#   - GPU(s) available
#   - No internet access
#
# Make sure all data, code, and dependencies are already in the
# workspace or baked into the container before submitting.

set -e

cd /home/user

export STEPS="${STEPS:-100000}"
export REWARD_GAP_BUDGET="${REWARD_GAP_BUDGET:-0.4}"
export REGENERATE_SUITE=1
bash scripts/method.sh
