# Reproduction Milestones

**Current: core_claim**

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

## Stop Justification
- Not stopped; submitting a full 100,000-step validation rerun for the corrected STARs pipeline.
