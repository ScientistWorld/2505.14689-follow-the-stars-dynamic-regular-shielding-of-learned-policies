# Evaluation

## Metrics

- **Buchi frequency:** Fraction of evaluated time steps in which the run visits the required Buchi region. Higher is better.
- **Average reward:** Mean reward per step over the evaluation horizon. Higher is better and is reported diagnostically.
- **Reward gap or reward closeness:** Difference from, or ratio to, the best per-instance average reward achievable by the nominal reward objective. Lower gap or higher closeness is better; this is the scored reward-preservation constraint.
- **Safety/objective violation rate:** Fraction of runs or steps that violate safety constraints or fail the required recurring-goal condition within the evaluation horizon. Lower is better.
- **Naive-baseline improvement:** Difference in Buchi frequency at matched reward-closeness thresholds against a method-agnostic naive runtime guide that increases exploration without targeted recurring-goal guidance. Higher is better.

## Baselines and Targets

Use the unmodified reward-optimized policy as the reward reference and sanity-check baseline. Use a naive stochastic guide as the main shielding-quality baseline: it should make the policy more exploratory without using a targeted mechanism for recurring-goal progress.

The paper's FactoryBot target setting is 383 random grid instances: 189 Far instances with reward and Buchi regions at l1-distance 0.7 to 0.9 times grid size, and 194 Close instances with distance 0.1 to 0.2 times grid size. The paper evaluates square grids with sizes 5 through 13 and reports results over 100,000 steps from a random initial state per instance.

Good performance means improving Buchi frequency over the nominal and naive baselines while keeping average reward close to the per-instance reward optimum. Because the paper's claim is a tradeoff, scores must include both recurring-goal benefit and reward/safety constraints.

## Evaluation Protocol

Generate FactoryBot gridworld instances with fixed seeds and preserve the Far/Close split. For each instance, evaluate a reward-optimized nominal policy and each submitted runtime-guidance method from the same random initial-state protocol and the same step horizon. Report aggregate metrics separately for Close and Far instances as diagnostics, then report an overall aggregate as the scored comparison.

Sweep the method's enforcement or intervention strength when it has such a parameter. For each reward-closeness threshold, compare the best recurring-goal frequency achieved by each method while remaining within that threshold. The evaluation should not import or depend on a submitted method implementation; it should call methods through a common action-distribution interface.
