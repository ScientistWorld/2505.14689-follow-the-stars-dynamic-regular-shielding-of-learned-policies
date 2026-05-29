# Reproduction Milestones

**Current: core_claim_plus**

## Progress Log

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
