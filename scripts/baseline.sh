#!/bin/bash
# Baselines.
#
# The two baselines -- the unshielded nominal policy ("unshielded") and the
# naive exploration guide ("apply_naive", best global mixing weight per
# reward budget) -- are computed by the scorers themselves on every
# evaluation, so they can never be edited by a method. baseline/ holds the
# same behaviours as ordinary runtime guides for development use.
#
# Usage: bash scripts/baseline.sh

set -e

cd /home/user

bash scripts/evaluate.sh
