# Evaluation Targets

This benchmark is FactoryBot-centered. All targets must be measured with method-agnostic evaluation code that can run any runtime guide through the same action-distribution interface.

## Primary: factorybot_buchi_reward_tradeoff

Tests whether a runtime guide can increase recurring-goal satisfaction while preserving the nominal reward objective on the paper's random FactoryBot gridworld distribution.

- **Metric:** `buchi_frequency` (higher is better)
- **Constraint metrics:** `average_reward` (higher is better), `reward_gap_to_instance_best` (lower is better), `safety_violation_rate` (lower is better)
- **How to run evaluation:** Evaluate each method on the fixed FactoryBot instance suite, separately aggregate Close and Far instances, and compute the best Buchi frequency achievable at each reward-closeness threshold.

## Constraint: factorybot_reward_preservation

Tests whether improvements in recurring-goal visits are obtained without simply sacrificing the reward objective the nominal policy was built to optimize.

- **Metric:** `reward_gap_to_instance_best` (lower is better)
- **Supporting metric:** `average_reward` (higher is better)
- **How to run evaluation:** Compare method rollouts against the per-instance best reward reference over the same initial-state protocol and horizon used for the primary benchmark.

## Constraint: factorybot_safety_compliance

Tests whether the runtime guide respects safety constraints while pursuing recurring goals and reward.

- **Metric:** `safety_violation_rate` (lower is better)
- **Supporting metric:** `valid_run_rate` (higher is better)
- **How to run evaluation:** During the same FactoryBot rollouts, count transitions into blocked/unsafe states or any state-action choices that violate the instance's safety constraints.

## Ablation: factorybot_vs_naive_baseline

Tests whether the recurring-goal improvement exceeds what can be obtained by generic stochastic exploration at matched reward levels.

- **Metric:** `buchi_frequency_gain_over_naive` (higher is better)
- **Constraint metric:** `matched_reward_gap` (lower is better)
- **How to run evaluation:** Run the same instance suite with a naive exploratory runtime guide and compare Buchi frequency only at reward-closeness thresholds where both methods satisfy the same reward constraint.
