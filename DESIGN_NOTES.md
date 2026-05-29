# Train/Test Evaluation Design Notes

## Checks

- Reviewed `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh`; train invokes `eval/train/` and writes `scoring/scores_train.json`, while test invokes `eval/test/` and writes `scoring/scores_test.json`.
- Checked the evaluators for method detachment. Both slices read the method-agnostic JSONL artifact passed on the command line instead of importing or rerunning `method/`.
- Checked for train/test cross-imports and paper-agreement metrics. The split evaluators duplicate local logic rather than importing each other, and the scored metrics measure Buchi frequency, reward preservation, naive-baseline gain, category robustness, and budget violations rather than closeness to published values.
- Confirmed no `scoring/scores_train.json` or `scoring/scores_test.json` stubs are present.
- Ran `bash -n scripts/evaluate_train.sh` and `bash -n scripts/evaluate_test.sh`.

## Changes

- Fixed a held-out leakage/gaming path in `eval/test/factorybot_eval_test.py`: the test evaluator no longer selects the best configuration on the test slice when train scores are missing. It now requires `scoring/scores_train.json` and applies the visible train-selected method/configuration set to held-out instances.
- Added `worst_category_buchi_frequency` and `worst_category_buchi_gain_over_naive` to both train and test scoring. These make the split harder to game by improving only the easier FactoryBot regime while hiding failures in the global mean.
- Added `reward_budget_violation_rate` to both train and test scoring. This catches methods that keep the mean reward gap acceptable while violating the reward-preservation constraint on individual instances.
- Added required `higher_is_better`, `coefficient`, and `description` fields for every scored metric in `scoring/reference.json`.

## Runtime Concerns For Runner Iteration

- `scripts/evaluate_test.sh` now requires train scores first. The runner should call `scripts/evaluate_train.sh` before `scripts/evaluate_test.sh`, or pass `TRAIN_SCORES` to a compatible visible train score file.
- The new category robustness metrics assume both FactoryBot categories are represented in each slice. The deterministic split was designed by category, but the runner should confirm the generated artifact contains both `close` and `far` instances after future method changes.
- The evaluators require the method artifact to include `unshielded` and `apply_naive` rows so gains and reward gaps remain comparable. Future methods can add new method names, but should preserve those baseline rows in the JSONL artifact or the scoring semantics degrade.
