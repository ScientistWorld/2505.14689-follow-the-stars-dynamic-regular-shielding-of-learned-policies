# Problem Definition

## Research Question

How can an already learned probabilistic policy for a finite robot-control environment be guided at runtime so that it satisfies safety and recurring-goal requirements while preserving the policy's original reward-seeking behavior?

The FactoryBot-centered benchmark asks this question in gridworlds where the nominal policy is trained or computed to maximize average reward without the recurring-goal objective. At evaluation time, the agent must still collect high reward but must also repeatedly visit a designated Buchi region and respect any safety constraints. A future method should be evaluated as a post-processing runtime guide: it may observe the current state/history and the nominal action distribution, but it should not retrain the nominal policy for the new objective during evaluation.

## Why It Matters

Autonomous systems often receive new correctness requirements after a policy has already been trained. Requiring full retraining for every new liveness goal, obstacle, or deployment constraint is expensive and brittle. A good runtime guide would let engineers update formal obligations while reusing the existing policy.

## Success Criteria

A successful solution should:

- Increase the frequency of required recurring-goal visits.
- Preserve average reward close to the per-instance reward optimum.
- Avoid safety violations and unsatisfied runtime objectives.
- Handle both Close and Far settings, where the reward region may be near or far from the required recurring-goal region.
- Be evaluated without relying on implementation details of any particular shielding algorithm.
