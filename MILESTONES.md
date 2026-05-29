# Reproduction Milestones

**Current: core_claim**

<!-- Milestone levels (update "Current" above as you progress):
  none             — just started, no meaningful progress yet
  method_runs      — the paper's method executes end-to-end without errors
  core_claim       — minimum experiment supports the paper's central claim
  core_claim_plus  — core claim reproduced on additional settings
  secondary_claims — secondary results or contributions reproduced
  majority         — more than half of reported results reproduced
  near_complete    — most results reproduced, only minor gaps remain
  full             — all reported results reproduced
-->

## Progress Log

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

## Stop Justification
- Completed at milestone `core_claim`.
