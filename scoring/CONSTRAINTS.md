# Scientist Constraints

These constraints define what future scientist agents must hold fixed when trying to improve the benchmark scores. They are intended to prevent trivial gains from changing the benchmark rather than improving runtime guidance.

## Problem Setting

The scientist must solve the same post-shielding problem: guide a pre-existing probabilistic policy at runtime in FactoryBot. The nominal policy must remain a reward-optimized policy that does not train directly on the Buchi objective used for evaluation. Retraining the nominal policy on the evaluation objective would sidestep the paper's runtime-guidance question.

## Data and Instances

The scientist must evaluate on the provided FactoryBot instance suite and its fixed random seeds. The suite should preserve the paper's structure: square grids of sizes 5 through 13, Close instances where reward and Buchi regions are near, and Far instances where they are separated. New generated instances may be used for development, but the reported score must use the fixed evaluation suite.

No external task data may be added to the evaluation. FactoryBot is procedurally generated, so extra public datasets are not relevant; using them would change the problem.

## Evaluation Protocol

The scientist must use the same rollout horizon, initial-state protocol, reward function, safety constraints, Buchi-region definitions, and Far/Close labels as the benchmark evaluation. They may not filter out hard instances, shorten runs only for their method, or tune per-instance using evaluation outcomes.

The method must be evaluated through the common runtime-guidance interface. Evaluation code must remain independent of the submitted method implementation and must not import from `method/`.

## Nominal Policy

The scientist must use the benchmark's provided nominal policy or nominal-policy generation procedure. The policy may be queried as a black-box action distribution during runtime guidance, but its weights, transition preferences, or training objective may not be changed for the reported score.

## Allowed Method Inputs

At evaluation time, a method may use the current FactoryBot state, execution history, the nominal action distribution, and the formal problem description supplied by the benchmark. It may not use hidden evaluation labels, future random choices, or rollout outcomes from the same evaluation seed before selecting actions.

## Compliance Checklist

- [ ] Reported scores use the fixed FactoryBot evaluation suite and Far/Close split.
- [ ] The nominal reward policy is not retrained or fine-tuned on the evaluation Buchi objective.
- [ ] Rollout horizon, initial-state protocol, rewards, safety rules, and Buchi regions match the benchmark evaluation.
- [ ] Evaluation code does not import from `method/`.
- [ ] No hard instances are removed or reweighted outside the benchmark scoring rules.
- [ ] Method decisions do not use future trajectory information or hidden evaluation outcomes.
