#!/bin/bash
set -euo pipefail
cd /home/user
python redteam/bootstrap.py
trap 'python redteam/restore.py' EXIT

# Existing paper-scale artifact, then full-scale honest-method checks.
if [ ! -f redteam/_state/checkpoints/factorybot_results.jsonl ]; then
    python redteam/compute.py --steps 100000 --workers 4
fi
bash redteam/reference_original/run.sh
python redteam/compute.py --steps 100000 --workers 4
for name in reference_seed_7 reference_seed_17 reference_seed_29 better_reward_accounting; do
    bash "redteam/$name/run.sh"
done

# All summary-only cases reuse the reference's actual trained rollouts.
for name in shortcut_no_guidance shortcut_low_enforcement shortcut_seed_replay \
    shortcut_fabricated_metrics shortcut_impossible_metrics shortcut_nan_reward \
    shortcut_null_metrics shortcut_weaken_baselines shortcut_drop_baselines \
    shortcut_train_selection shortcut_filter_far shortcut_replace_nominal \
    shortcut_write_final_scores; do
    bash "redteam/$name/run.sh"
done
python redteam/report.py
