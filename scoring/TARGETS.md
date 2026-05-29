# Evaluation Targets

This benchmark is FactoryBot-centered. All targets must be measured with method-agnostic evaluation code that can run any runtime guide through the same action-distribution interface.

## Primary and Constraints: factorybot_buchi_reward_tradeoff

Tests whether a runtime guide can increase recurring-goal satisfaction while preserving the nominal reward objective on the paper's random FactoryBot gridworld distribution.

- **Metric:** `buchi_frequency` (higher is better)
- **Constraint metric:** `reward_gap_to_nominal` (lower is better)
- **Ablation metric:** `buchi_frequency_gain_over_naive` (higher is better)
- **How to run evaluation:** Evaluate each method on the fixed FactoryBot instance suite and compute aggregate rollout metrics. The recurring-goal metric must improve over both the unshielded nominal policy and the naive exploratory baseline while the reward gap to the nominal reward policy remains within the configured budget. Interference and override rates are emitted as diagnostics, not scored targets.
