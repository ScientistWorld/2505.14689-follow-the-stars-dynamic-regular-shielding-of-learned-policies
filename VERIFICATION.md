# Verification Report

## Initial Assessment

The workspace starts this final check at `core_claim_plus`. That milestone is still justified by the already completed 50-instance, 100,000-step FactoryBot run: the implemented method contains the paper's STARs runtime distribution update and a FactoryBot Buchi strategy-template specialization, and the scored artifact shows higher Buchi frequency than the nominal and naive baselines while tracking reward loss.

The previous iteration also made two important protocol improvements after that successful run: it changed rollouts to sample a random initial state and expanded the fixed FactoryBot suite to the paper-scale 383-instance Close/Far split.

## Issues Found

- Critical for final sign-off: `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` still correspond to the prior 50-instance artifact, while the current tracked suite contains 383 instances. The milestone should not be lowered because the prior result supports `core_claim_plus`, but the current gym baseline must be regenerated before this can be marked fully ready.
- Minor: generated Python bytecode caches existed under source/data/eval folders. They were ignored by git but cluttered the workspace.

No method-agnostic leak was found in `briefing/problem.md`, `briefing/evaluation.md`, or `scoring/EXPERIMENTS.md`. The evaluation code does not import from `method/`, `scripts/download.sh` is self-contained and `shared/`-free, and the scoring rubric has no wall-clock or paper-deviation metric.

## Fixes Applied

- Removed generated `__pycache__` directories from source/data/eval/scoring folders.
- Kept `action.yaml` in submit mode so the queued CPU job regenerates main, train, and test scores from the current 383-instance, random-start protocol.
- Re-ran `python validate.py --compare`; structure and scoring validation pass, with the caveat that the compared scores are the stale 50-instance artifact described above.

## Final Judgment

The workspace is structurally sound and close to final, but it should not be permanently marked done until the submitted CPU validation run refreshes `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` for the current paper-scale suite. From-scratch and improve-mode separation is otherwise clean: problem/evaluation files describe the runtime-guidance task without exposing the STARs implementation, and evaluation reads method artifacts rather than method code.

- Milestone: core_claim_plus
- Ready for gym use: partial
- Confidence: medium
- Key limitation: current score artifacts are stale relative to the tracked 383-instance, random-start FactoryBot protocol.
