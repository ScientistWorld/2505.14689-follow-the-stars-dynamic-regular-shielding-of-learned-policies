# Overview

- **Paper ID:** 2505.14689
- **Title:** Follow the STARs: Dynamic omega-Regular Shielding of Learned Probabilistic Policies
- **Domain:** Formal methods for reinforcement learning / runtime shielding
- **TL;DR:** The paper studies how to enforce omega-regular correctness obligations over an already learned probabilistic policy while preserving as much reward-seeking behavior as possible.

## Short Summary

The paper addresses runtime shielding for learned autonomous agents when the required specification includes liveness, not only safety. Its central setting is a black-box nominal policy that already optimizes a task reward, plus a separate runtime monitor/controller that must keep executions compliant with formal objectives as deployment conditions change. The FactoryBot benchmark is the most reproducible core setting: a robot moves in random gridworlds, seeks high average reward, and must repeatedly visit a specified Buchi region under static or changing constraints. The headline empirical claim is that the shield can raise Buchi-visit frequency while retaining reward better than a naive stochastic exploration baseline.

## Key Results

- FactoryBot uses 383 random square-grid instances, split into 189 Far and 194 Close instances according to the distance between the reward region and the Buchi region.
- Each FactoryBot instance is evaluated over 100,000 steps from a random initial state, reporting Buchi-region visit frequency and average reward.
- The paper also reports secondary evidence on Overcooked-AI scalability and LunarLander performance, including 87% helipad landings over 200 LunarLander seeds for the liveness shielded policy.

---

# Problem Definition

## Research Question

How can an already learned probabilistic policy for a finite robot-control environment be guided at runtime so that it satisfies recurring-goal (liveness) requirements while preserving the policy's original reward-seeking behavior?

The FactoryBot-centered benchmark asks this question in gridworlds where the nominal policy is computed to maximize average reward without the recurring-goal objective. At evaluation time, the robot must still collect reward but must also repeatedly visit a designated Büchi cell. A method is a post-processing **runtime guide**: at each step it sees the current state, its own execution history, the nominal action distribution, and the known transition graph with the Büchi cell, and it returns the action distribution to execute. It may not retrain or replace the nominal policy, and it is not told where the reward is.

## Why It Matters

Autonomous systems often receive new correctness requirements after a policy has already been trained. Requiring full retraining for every new liveness goal, obstacle, or deployment constraint is expensive and brittle. A good runtime guide would let engineers update formal obligations while reusing the existing policy.

## Success Criteria

A successful guide should:

- Increase how often the robot visits the required Büchi cell.
- Keep the average reward within a prescribed budget of what the unmodified nominal policy earns on the same grid — at several budgets, from tight (0.1) to loose (0.4).
- Achieve this on both Close grids (reward near the Büchi cell) and Far grids (reward far from it), where the compromise is much harder.
- Visit the Büchi cell at a meaningful rate on as many grids as possible, not only on average.
- Work from information available at runtime; it must not depend on knowing the evaluation grids or random numbers in advance.

---

# Paper's Method

## Key Contribution

The paper introduces Strategy-Template-based Adaptive Runtime Shields (STARs), a dynamic post-shielding framework for enforcing omega-regular specifications over learned probabilistic policies. Its distinctive feature is a tunable enforcement parameter, gamma, that controls how strongly the runtime shield biases the policy toward formal obligations.

## Approach

STARs starts from a known finite MDP and an omega-regular objective represented as a parity condition. It computes a winning strategy template for the induced game; the template separates obligations into unsafe actions, co-live actions to eventually avoid, and live action groups that must eventually be taken when their source states recur.

At runtime, STARs takes the nominal policy's action distribution in the current state and modifies it using counters derived from the execution history. Unsafe actions receive zero probability. Co-live actions are downweighted as they are sampled. Live groups are upweighted when their source states are repeatedly visited without taking one of the group's actions. The result is normalized into a shielded action distribution. The enforcement parameter gamma and threshold theta determine how aggressively these probability changes occur and can be changed at runtime.

For changing specifications, STARs relies on compositional strategy templates: newly arriving omega-regular objectives can be integrated into the existing template when the current run remains in the combined winning region. For action failures, unavailable actions can be treated as temporarily or persistently excluded from the template.

In this reproduction, the implemented FactoryBot path uses the paper's Büchi specialization of `ParityTemplate`: because each generated grid is a strongly connected winning region and the objective is to visit the Büchi set infinitely often, template synthesis reduces to a reachability template. The code partitions states into attractor layers toward the Büchi cell and creates live groups from each layer to lower layers (`method/template_synthesis.py`), then applies the STARs runtime distribution update from Definition 2 (`method/stars.py`). The nominal policy is generated by average-reward relative value iteration over the reward-only FactoryBot MDP, with epsilon perturbation to keep the policy probabilistic; the scorers compute it themselves.

ApplySTARs is packaged as a runtime guide (`method/stars_guide.py`): for each grid it synthesizes the template from the transition graph and Büchi cell, and at every step shields the nominal distribution it is handed. `method/factorybot_method.py` sweeps gamma over the paper's grid (1e-3, 1e-2, 0.05, 0.1, 0.2, 0.5, 1) with theta = 0.02 on the visible 383-grid suite at 100,000 steps (the Fig. 4a experiment), picks one global gamma per reward budget, and writes the guide spec `checkpoints/guides/apply_stars.json` that the scorers load.

## Main Claims

- **Primary claim:** A runtime shield can enforce omega-regular objectives, including liveness, over a pre-computed probabilistic policy while preserving much of the policy's reward performance.
- **FactoryBot empirical claim:** On random gridworld instances, increasing enforcement increases Buchi-region visit frequency, with an explicit tradeoff against average reward, and the proposed shield achieves higher Buchi frequency than a naive exploration-style shield at comparable reward levels.
- **Dynamic-adaptation claim:** The shield can accommodate changing objectives or action availability without retraining the nominal policy, provided the updated objective remains satisfiable from the current setting.
- **Scalability/application claims:** The same framework scales to large finite game graphs in Overcooked-AI and can improve helipad landing rates in a coarse-abstraction LunarLander setting.

---

# Evaluation

## What is measured

A submitted method is a **runtime guide**: at every step it receives the current state and the nominal policy's action distribution and returns the action distribution to execute. The scorer runs the guide itself, inside its own simulator, with its own nominal policy and its own random numbers, and computes every number from the resulting trajectories. Nothing a method writes (rollout rows, metrics, score files, baseline rows, instance lists) is read.

Each guide is run on every grid once per **reward budget** eps in {0.1, 0.2, 0.3, 0.4}, for 100,000 steps from a random start state. The unshielded nominal policy is run on the same grid with the same random numbers; its average reward is the comparator. A run *meets the budget* when its average reward is at most eps below the nominal's.

## Scored metrics

- **`matched_reward_buchi_frequency`** (coefficient 1.0, primary): mean over budgets and grids of the run's Büchi-region visit frequency (fraction of steps that end in the Büchi cell), counted as 0 for runs that miss the budget.
- **`matched_reward_gain_over_naive`** (0.5): the above minus the naive baseline's value.
- **`worst_category_matched_reward_buchi_frequency`** (0.5): the lower of the Close-grid and Far-grid values of the primary metric.
- **`liveness_success_rate`** (0.25): fraction of (grid, budget) runs that meet the budget *and* visit the Büchi region with frequency at least 1/|Q|, where |Q| is the grid's number of free cells.

The rank of a method is the sum over these metrics of coefficient times (method value − reference value). Reward preservation is a hard per-run constraint inside every metric: a run that loses too much reward contributes nothing, so no metric rewards doing nothing or rewards breaking the budget.

**Failure rule.** If a guide raises an exception, returns something that is not a mapping, names an unknown action, or returns probabilities that are negative, non-finite, or do not sum to 1 (tolerance 1e-6) on any step of any run, the method is scored as failed: every frequency/rate metric is 0 and the gain is minus the naive baseline's value.

Diagnostics (per budget and per Close/Far category): budget-violation rate, mean reward gap, ungated Büchi frequency, Büchi frequency among runs within budget (the paper's Fig. 4b averaging), average reward, total-variation distance to the nominal, and override rate.

## Baselines (computed by the scorer)

- **`unshielded`**: the nominal policy unchanged.
- **`apply_naive`**: untargeted extra exploration — the nominal mixed with the uniform distribution. For each budget the scorer uses the best global mixing weight from {0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0} on the scored grids (the strongest such baseline).

## Environment

- Square grids of size 5–13 with 12% walls (free cells connected), one Büchi cell and one reward cell. **Close** grids place the reward at l1-distance 0.1–0.2 × size from the Büchi cell, **Far** grids at 0.7–0.9 × size.
- Actions up/down/left/right move deterministically; moving into a wall or the boundary leaves the robot in place.
- Reward: +1 for a move that enters the reward cell, −0.01 every step.
- Nominal policy: average-reward optimal for the reward alone (relative value iteration), with 4% of probability spread uniformly over all actions.

## Submitting a guide

Write `checkpoints/guides/<name>.json`:

```json
{"name": "my_guide", "module": "path/to/guide.py", "factory": "make_guide", "params": {}}
```

`module` is relative to the workspace root. For every (grid, budget) run the scorer imports the module afresh (no module state survives between runs) and calls `factory(model, budget, params)`, which returns an object with:

- `act(state, nominal) -> {action: probability}` — `nominal` is a read-only mapping of the nominal distribution at `state`.
- `observe(state, action, next_state, reward)` — called after the scorer samples the action and simulates the move.

`model` exposes `size`, `walls`, `states`, `actions`, `buchi` (frozenset of cells), `successor(state, action)` and `nominal(state)`. The reward cell, the Close/Far label and the random numbers are not exposed. The names `unshielded` and `apply_naive` are reserved.

## Train and test

- `bash scripts/evaluate_train.sh` (and `scripts/evaluate.sh`) score every spec in `checkpoints/guides/` on the visible suite: the 383 grids of `data/factorybot_suite.json` (194 Close, 189 Far) with visible rollout seeds. Write `scoring/scores_train.json` / `scoring/scores.json`.
- `bash scripts/evaluate_test.sh` (no arguments) scores every spec on 256 held-out grids (128 Close, 128 Far) from the same generator, with held-out rollout seeds, and writes `scoring/scores_test.json`.
- `data/factorybot_rollout.py` reproduces the rollout protocol for development (`GuideModel`, `rollout_guide`, `rollout_policy`).

A full scoring pass costs roughly 4 × (number of grids) × 100,000 guide calls per method; it runs on CPU and uses all available cores.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:10] - method_runs
- Read the paper and identified FactoryBot as the tractable core claim: dynamic liveness shielding should increase Buchi visits while retaining reward better than naive exploration.
- Implemented the paper's STARs runtime update with strategy-template live groups, history counters, thresholding, and normalization.
- Ran a local smoke test on a short FactoryBot rollout; the method and evaluator execute end-to-end and write `scoring/scores.json`.

### [2026-05-29 03:58] - core_claim
- Completed a CPU compute job over the fixed FactoryBot suite at 30,000 steps per instance.
- STARs achieved substantially higher Buchi frequency than both the unshielded policy and the naive exploratory guide.
- The STARs run also preserved average reward above the naive guide, supporting the paper's central benefit-plus-constraint claim on the scaled FactoryBot setting.

### [2026-05-29 04:02] - core_claim
- Re-ran the FactoryBot reproduction at the paper's 100,000-step rollout horizon.
- The longer run preserved the same conclusion: STARs improved recurring-goal frequency by more than 7x over the naive guide while retaining higher average reward than the naive guide.
- Packaged scripts, data generation, evaluation, scoring, and documentation are complete for the core FactoryBot benchmark.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 3 total (3 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 00:00] - method_runs
- Implemented the STARs runtime distribution update with history counters, thresholding, and normalization.
- Ran the FactoryBot method/evaluation loop end to end.

### [2026-05-29 00:00] - core_claim
- Completed a 100,000-step FactoryBot reproduction job.
- ApplySTARs increased Buchi frequency to 0.12894 versus 0.01762 for ApplyNaive while maintaining non-collapsed average reward.

### [2026-05-29 00:00] - core_claim_plus
- Completed job `ce1da14c-3e3` on a broader 30-instance FactoryBot suite spanning grid sizes 5, 7, 9, 11, and 13 with balanced Close/Far cases.
- Fixed the evaluator so STARs gamma selection is based on full-suite aggregate reward instead of filtering out low-reward instances.
- Corrected expanded-suite score: ApplySTARs Buchi frequency 0.07349 versus 0.02150 for ApplyNaive, with average reward 0.39555 versus 0.42373 for ApplyNaive.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 29m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 5m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 4 total (4 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 1m | **GPU**: 0.0h
- **Jobs**: 5 total (5 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 1m | **GPU**: 0.0h
- **Jobs**: 5 total (5 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 5 total (5 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

### [2026-05-29 04:05] - core_claim_plus
- Main scoring now reports the declared category-robustness and reward-budget constraint metrics in addition to the primary Buchi/reward tradeoff.
- `python validate.py --compare`, `scripts/evaluate.sh`, and Python bytecode compilation all pass after the scoring-completeness fix.

### [2026-05-29 04:12] - core_claim_plus
- Final verification confirmed method/problem separation, reusable evaluation, train/test scoring consistency, shared-free downloads, and reasonable metric coefficients.
- Removed stale tracked trajectory logs from the repository index and cleaned generated Python bytecode caches.

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 15m | **GPU**: 0.0h
- **Jobs**: 7 total (6 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

### [2026-05-29 04:05] - core_claim_plus
- Main scoring now reports the declared category-robustness and reward-budget constraint metrics in addition to the primary Buchi/reward tradeoff.
- `python validate.py --compare`, `scripts/evaluate.sh`, and Python bytecode compilation all pass after the scoring-completeness fix.

### [2026-05-29 04:12] - core_claim_plus
- Final verification confirmed method/problem separation, reusable evaluation, train/test scoring consistency, shared-free downloads, and reasonable metric coefficients.
- Removed stale tracked trajectory logs from the repository index and cleaned generated Python bytecode caches.

### [2026-05-29 04:20] - core_claim_plus
- Fixed the FactoryBot rollout protocol to sample the initial state randomly for each instance, matching the paper's evaluation description.
- Expanded the procedural FactoryBot suite generator to the paper's original 383-instance Close/Far split: 194 Close and 189 Far instances over grid sizes 5 through 13.
- Updated `scripts/run.sh` to regenerate the suite and rerun the method before evaluation, so submission no longer depends on an ignored preexisting checkpoint artifact.
- Submitting a CPU job at the paper's 100,000-step rollout horizon to verify whether the current `core_claim_plus` result holds under the original instance count and corrected random-start protocol.

### [2026-05-29 05:00] - core_claim_plus
- Cancelled the first paper-scale CPU validation after 40 minutes because the runner produced no flushed result rows and was unlikely to finish within the test-node window.
- Cached STARs live-group template lookups and added per-instance progress/flushing to the method runner, preserving the same STARs computation while removing repeated bookkeeping overhead.
- A one-instance 100,000-step smoke run completed successfully after the fix; resubmitting the paper-scale 383-instance validation.

### [2026-05-29 05:50] - core_claim_plus
- Compute job `56dfe94c-d10` completed the full 383-instance FactoryBot random-start suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11431 at reward gap 0.34310, versus `apply_naive` Buchi frequency 0.03910 at reward gap 0.36740.
- The final main/train/test score files now all reflect the current 383-instance protocol and pass `python validate.py --compare`.

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 8m | **GPU**: 0.0h
- **Jobs**: 1 total (1 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

### [2026-05-29 04:05] - core_claim_plus
- Main scoring now reports the declared category-robustness and reward-budget constraint metrics in addition to the primary Buchi/reward tradeoff.
- `python validate.py --compare`, `scripts/evaluate.sh`, and Python bytecode compilation all pass after the scoring-completeness fix.

### [2026-05-29 04:12] - core_claim_plus
- Final verification confirmed method/problem separation, reusable evaluation, train/test scoring consistency, shared-free downloads, and reasonable metric coefficients.
- Removed stale tracked trajectory logs from the repository index and cleaned generated Python bytecode caches.

### [2026-05-29 04:20] - core_claim_plus
- Fixed the FactoryBot rollout protocol to sample the initial state randomly for each instance, matching the paper's evaluation description.
- Expanded the procedural FactoryBot suite generator to the paper's original 383-instance Close/Far split: 194 Close and 189 Far instances over grid sizes 5 through 13.
- Updated `scripts/run.sh` to regenerate the suite and rerun the method before evaluation, so submission no longer depends on an ignored preexisting checkpoint artifact.
- Submitting a CPU job at the paper's 100,000-step rollout horizon to verify whether the current `core_claim_plus` result holds under the original instance count and corrected random-start protocol.

### [2026-05-29 05:00] - core_claim_plus
- Cancelled the first paper-scale CPU validation after 40 minutes because the runner produced no flushed result rows and was unlikely to finish within the test-node window.
- Cached STARs live-group template lookups and added per-instance progress/flushing to the method runner, preserving the same STARs computation while removing repeated bookkeeping overhead.
- A one-instance 100,000-step smoke run completed successfully after the fix; resubmitting the paper-scale 383-instance validation.

### [2026-05-29 05:50] - core_claim_plus
- Compute job `56dfe94c-d10` completed the full 383-instance FactoryBot random-start suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11431 at reward gap 0.34310, versus `apply_naive` Buchi frequency 0.03910 at reward gap 0.36740.
- The final main/train/test score files now all reflect the current 383-instance protocol and pass `python validate.py --compare`.

</details>

### Iteration 11: claude-opus-5-5 (hardener)
- **Milestone**: `core_claim_plus` | **Status**: done
- **Working time**: 27m | **GPU**: 0.0h
- **Jobs**: 2 total (2 completed, 0 failed)

<details>
<summary>Progress Log</summary>

### [2026-05-29 03:17] - core_claim
- Existing 100,000-step FactoryBot job supports the core STARs tradeoff claim.
- Corrected the generated FactoryBot Close/Far distance bands and reward-gap scoring scale before submitting a validation rerun on the expanded 50-instance suite.
- Continuation audit found and fixed baseline coupling to `method/`; validation still passes.

### [2026-05-29 03:35] - method_runs
- Continuation audit found that the existing method used the STARs runtime reweighting formula but hand-built the FactoryBot live groups as a distance heuristic.
- Replaced that path with an explicit Büchi ReachTemplate/ParityTemplate specialization that synthesizes live groups from attractor partitions, and moved the nominal reward policy to a computed average-reward policy in `data/`.
- A 5-step smoke run over the corrected 50-instance suite completed and evaluated successfully; submitting a 100,000-step CPU validation job before restoring `core_claim`.

### [2026-05-29 03:49] - core_claim
- Ran the corrected STARs pipeline over the full 50-instance FactoryBot suite for a 2,000-step validation horizon.
- `apply_stars` reached Buchi frequency 0.113 at reward gap 0.336, versus `apply_naive` Buchi frequency 0.039 at reward gap 0.358.
- The result comes from synthesized Büchi live groups and the computed average-reward nominal policy, so the corrected implementation now supports the core reward-versus-liveness claim.

### [2026-05-29 03:50] - core_claim
- Continuation audit confirmed the implementation contains the paper's STARs runtime reweighting and the FactoryBot Büchi ReachTemplate synthesis rather than a surrogate model.
- `python validate.py --compare`, standalone `scripts/evaluate.sh`, and Python bytecode compilation all pass on the corrected 2,000-step artifact.
- Submitting the corrected 50-instance suite at the paper's 100,000-step rollout horizon to try to restore `core_claim_plus`.

### [2026-05-29 03:50] - core_claim_plus
- Compute job `983173c2-f20` completed the corrected 50-instance FactoryBot suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11381 at reward gap 0.33948, versus `apply_naive` Buchi frequency 0.03985 at reward gap 0.35620.
- This restores `core_claim_plus`: the core reward-versus-liveness claim now holds at the paper's rollout horizon with the corrected template synthesis and nominal-policy path.

### [2026-05-29 04:05] - core_claim_plus
- Main scoring now reports the declared category-robustness and reward-budget constraint metrics in addition to the primary Buchi/reward tradeoff.
- `python validate.py --compare`, `scripts/evaluate.sh`, and Python bytecode compilation all pass after the scoring-completeness fix.

### [2026-05-29 04:12] - core_claim_plus
- Final verification confirmed method/problem separation, reusable evaluation, train/test scoring consistency, shared-free downloads, and reasonable metric coefficients.
- Removed stale tracked trajectory logs from the repository index and cleaned generated Python bytecode caches.

### [2026-05-29 04:20] - core_claim_plus
- Fixed the FactoryBot rollout protocol to sample the initial state randomly for each instance, matching the paper's evaluation description.
- Expanded the procedural FactoryBot suite generator to the paper's original 383-instance Close/Far split: 194 Close and 189 Far instances over grid sizes 5 through 13.
- Updated `scripts/run.sh` to regenerate the suite and rerun the method before evaluation, so submission no longer depends on an ignored preexisting checkpoint artifact.
- Submitting a CPU job at the paper's 100,000-step rollout horizon to verify whether the current `core_claim_plus` result holds under the original instance count and corrected random-start protocol.

### [2026-05-29 05:00] - core_claim_plus
- Cancelled the first paper-scale CPU validation after 40 minutes because the runner produced no flushed result rows and was unlikely to finish within the test-node window.
- Cached STARs live-group template lookups and added per-instance progress/flushing to the method runner, preserving the same STARs computation while removing repeated bookkeeping overhead.
- A one-instance 100,000-step smoke run completed successfully after the fix; resubmitting the paper-scale 383-instance validation.

### [2026-05-29 05:50] - core_claim_plus
- Compute job `56dfe94c-d10` completed the full 383-instance FactoryBot random-start suite at 100,000 steps per instance.
- `apply_stars` reached Buchi frequency 0.11431 at reward gap 0.34310, versus `apply_naive` Buchi frequency 0.03910 at reward gap 0.36740.
- The final main/train/test score files now all reflect the current 383-instance protocol and pass `python validate.py --compare`.

### [2026-11-08] - core_claim_plus
- Hardening iteration: scorers now run each submitted runtime guide themselves on scorer-owned grids (256 hidden test grids), nominal policy, random numbers and baselines; scored metrics are Büchi frequency at matched reward (budgets 0.1-0.4, over-budget runs count as zero), gain over naive, worst Close/Far category, and per-run liveness success.
- Job `4e266a0c-988`: ApplySTARs (unchanged algorithm, γ tuned per budget on the visible 383-grid suite) scores matched frequency 0.072 on the hidden test vs naive 0.027 and unshielded 0.017, beating naive at every budget; a genuinely better guide scores +0.450, a dynamic-γ STARs variant +0.025 (seed spread 0.0014), and every iteration-10 shortcut now scores below the reference, fails, or leaves scores unchanged. Details in `HARDENING.md`.

</details>


---

# Reproduction Milestones

**Current: core_claim_plus**

## Stop Justification
- Completed at milestone `core_claim_plus`.
