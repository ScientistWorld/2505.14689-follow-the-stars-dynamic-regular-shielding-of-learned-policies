# Evaluation Targets

This benchmark is FactoryBot-centered. All targets are computed by the scorers (`eval/train/`, `eval/test/`), which run each submitted runtime guide through the common guide interface on their own simulator, nominal policy, grids and random numbers.

## Primary and Constraints: factorybot_buchi_reward_tradeoff

Tests whether a runtime guide can increase recurring-goal satisfaction while preserving the nominal reward objective on the paper's random FactoryBot gridworld distribution, across reward budgets 0.1–0.4.

- **Primary metric:** `matched_reward_buchi_frequency` (higher is better) — Büchi frequency averaged over budgets and grids, with runs that break the reward budget counted as 0.
- **Constraint (embedded):** the per-run reward budget relative to the nominal policy on the same grid and random numbers; a violated budget zeroes the run in every scored metric. Violation rates are reported as diagnostics.
- **Comparison metric:** `matched_reward_gain_over_naive` (higher is better) — advantage over the scorer's naive exploration guide at its best mixing weight per budget.
- **Robustness metric:** `worst_category_matched_reward_buchi_frequency` (higher is better) — the weaker of Close and Far grids.
- **Constraint-and-liveness metric:** `liveness_success_rate` (higher is better) — fraction of runs that meet the budget and visit the Büchi cell at frequency ≥ 1/|Q|.
- **Failure rule:** invalid action distributions or crashes score the method as failed.
- **How to run evaluation:** `bash scripts/evaluate_train.sh` (visible suite) and `bash scripts/evaluate_test.sh` (held-out grids), both with no arguments; they score every spec in `checkpoints/guides/`. Interference (total variation to the nominal) and override rates are diagnostics, not scored.
