# Reproduction Milestones

**Current: method_runs**

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

## Stop Justification
- Not stopped.
