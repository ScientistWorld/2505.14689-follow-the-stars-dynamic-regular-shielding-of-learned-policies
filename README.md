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

---

# Paper's Method

## Key Contribution

The paper introduces Strategy-Template-based Adaptive Runtime Shields (STARs), a dynamic post-shielding framework for enforcing omega-regular specifications over learned probabilistic policies. Its distinctive feature is a tunable enforcement parameter, gamma, that controls how strongly the runtime shield biases the policy toward formal obligations.

## Approach

STARs starts from a known finite MDP and an omega-regular objective represented as a parity condition. It computes a winning strategy template for the induced game; the template separates obligations into unsafe actions, co-live actions to eventually avoid, and live action groups that must eventually be taken when their source states recur.

At runtime, STARs takes the nominal policy's action distribution in the current state and modifies it using counters derived from the execution history. Unsafe actions receive zero probability. Co-live actions are downweighted as they are sampled. Live groups are upweighted when their source states are repeatedly visited without taking one of the group's actions. The result is normalized into a shielded action distribution. The enforcement parameter gamma and threshold theta determine how aggressively these probability changes occur and can be changed at runtime.

For changing specifications, STARs relies on compositional strategy templates: newly arriving omega-regular objectives can be integrated into the existing template when the current run remains in the combined winning region. For action failures, unavailable actions can be treated as temporarily or persistently excluded from the template.

In this reproduction, the implemented FactoryBot path uses the paper's Büchi specialization of `ParityTemplate`: because each generated grid is a strongly connected winning region and the objective is to visit the Büchi set infinitely often, template synthesis reduces to a reachability template. The code partitions states into attractor layers toward the Büchi cell and creates live groups from each layer to lower layers, then applies the STARs runtime distribution update from Definition 2. The nominal policy is generated by average-reward relative value iteration over the reward-only FactoryBot MDP, with epsilon perturbation to keep the policy probabilistic.

## Main Claims

- **Primary claim:** A runtime shield can enforce omega-regular objectives, including liveness, over a pre-computed probabilistic policy while preserving much of the policy's reward performance.
- **FactoryBot empirical claim:** On random gridworld instances, increasing enforcement increases Buchi-region visit frequency, with an explicit tradeoff against average reward, and the proposed shield achieves higher Buchi frequency than a naive exploration-style shield at comparable reward levels.
- **Dynamic-adaptation claim:** The shield can accommodate changing objectives or action availability without retraining the nominal policy, provided the updated objective remains satisfiable from the current setting.
- **Scalability/application claims:** The same framework scales to large finite game graphs in Overcooked-AI and can improve helipad landing rates in a coarse-abstraction LunarLander setting.

---

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


---

# Reproduction Milestones

**Current: core_claim_plus**

## Stop Justification
- Completed at milestone `core_claim_plus`.
