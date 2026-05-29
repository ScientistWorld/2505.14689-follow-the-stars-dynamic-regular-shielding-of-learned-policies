# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

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

## Stop Justification
- Not stopping in this turn; final verification found that the current score artifacts still correspond to the prior 50-instance run after the tracked code/data were moved to the 383-instance random-start protocol. Submitting the paper-scale CPU validation job while retaining the previously verified milestone `core_claim_plus`.
