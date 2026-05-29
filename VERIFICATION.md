# Verification Report

## Initial Assessment

The workspace starts this final check at `core_claim_plus`. That milestone is justified by the completed FactoryBot runs: the implemented method contains the paper's STARs runtime distribution update and a FactoryBot Buchi strategy-template specialization, and the scored artifact shows higher Buchi frequency than the nominal and naive baselines while tracking reward loss.

The final validation run now uses the paper-scale 383-instance Close/Far split, random initial states, and 100,000 rollout steps per instance.

## Issues Found

- Resolved: `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` were stale relative to the current 383-instance suite at the start of final verification. Job `56dfe94c-d10` regenerated all three score files from the current paper-scale protocol.
- Operational: the first 383-instance CPU validation was cancelled after 40 minutes because the STARs runner produced no flushed JSONL rows and was unlikely to complete within the test-node window.
- Minor: generated Python bytecode caches existed under source/data/eval folders. They were ignored by git but cluttered the workspace.
- Minor: system job and trajectory logs were tracked in git even though they are scheduler artifacts, not reusable benchmark inputs.

No method-agnostic leak was found in `briefing/problem.md`, `briefing/evaluation.md`, or `scoring/EXPERIMENTS.md`. The evaluation code does not import from `method/`, `scripts/download.sh` is self-contained and `shared/`-free, and the scoring rubric has no wall-clock or paper-deviation metric.

## Fixes Applied

- Removed generated `__pycache__` directories from source/data/eval/scoring folders.
- Cached live-group edge/source lookups inside `StarShield`, which preserves the same STARs distribution and counter semantics while avoiding repeated set construction in every rollout step.
- Added per-instance progress logging and row flushing to the method runner so long CPU validations visibly progress and keep partial artifacts under preemption.
- Removed tracked scheduler job/trajectory logs from the git index and added `jobs/` to `.gitignore`.
- Re-ran `python validate.py --compare`; structure and scoring validation pass against the refreshed 383-instance score artifacts.

## Final Judgment

The workspace is ready to serve as a research gym. From-scratch and improve-mode separation is clean: problem/evaluation files describe the runtime-guidance task without exposing the STARs implementation, and evaluation reads method artifacts rather than method code. The refreshed main/train/test scores all use the current 383-instance, random-start, 100,000-step FactoryBot protocol.

- Milestone: core_claim_plus
- Ready for gym use: yes
- Confidence: high
- Key limitation: secondary claims beyond the FactoryBot reward/liveness tradeoff were not reproduced.
