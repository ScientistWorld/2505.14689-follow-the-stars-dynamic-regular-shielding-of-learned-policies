#!/bin/bash
# Download all data and models needed for this environment.
#
# Run on a node with internet access BEFORE building the container
# or submitting compute jobs.
#
# This script should be idempotent — safe to run multiple times.
# It should skip files that already exist.
#
# Update the storage estimate below as you add downloads.
#
# Estimated total download size: 0 GB
# Estimated disk usage after extraction: <1 MB
#
# This paper-centered reproduction uses procedurally generated data, so there
# are no external datasets or model weights to fetch.

set -e

cd /home/user

python - <<'PY'
from pathlib import Path
from data.factorybot import write_suite

path = Path("data/factorybot_suite.json")
if not path.exists():
    write_suite(path)
PY
