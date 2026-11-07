# FactoryBot scoring audit

**Better results can score higher, but scientific quality does not determine the ranking.** A genuine runtime-guide improvement gains **+0.884458** over the reference. Removing the recurring-goal guide also gains **+0.105468**, despite making no Buchi visits in 92/192 test instances, including 91/95 Far instances. The weaker method should lose. Its gain is over 620 times the measured seed spread. This failure exists before any fabricated measurements or changed evaluation inputs.

All scores below use the six coefficients in `scoring/reference.json`, experiment weight 1, and the actual reference in `scoring/scores_test.json`. Define `S = sum(coefficient * metric)` and `delta = S(candidate) - S(reference)`. The reference has **S = -0.132914497478** and **delta = 0**. Higher is better. Historical visual estimates in `reference.json` are not substituted for the recorded comparator. Full precision results are in [summary.json](redteam/summary.json).

**Quality checks.** All actual rollouts used the full 383-instance suite, 100,000 steps, the original reward function, and the original initialization protocol. The unchanged test selected 192 instances: 97 Close and 95 Far. Only the explicitly labelled filtering shortcut reduced coverage.

| Method / runnable case | Mean Buchi frequency | Mean reward gap | Worst-category frequency | Budget violations | Test delta |
|---|---:|---:|---:|---:|---:|
| [Reference](redteam/reference_original/run.sh), gamma=1 | 0.110708 | 0.356262 | 0.016314 | 45.833% | 0 |
| [Genuine improvement: reward accounting](redteam/better_reward_accounting/run.sh) | 0.371727 | 0.312478 | 0.340628 | 0% | **+0.884458** |
| [Shortcut: no guidance](redteam/shortcut_no_guidance/run.sh), key idea removed | 0.011963 | 0 | 0.000000421 | 0% | **+0.105468** |
| [Shortcut: low enforcement](redteam/shortcut_low_enforcement/run.sh), gamma=0.03 only | 0.038253 | 0.083497 | 0.000081 | 0% | **+0.130476** |
| Original naive baseline | 0.036817 | 0.372726 | 0.000390 | 53.125% | -0.175850 |

The genuine improvement accumulates reward credit before funding complete recurring-goal excursions. It keeps the original reward-only nominal policy fixed and bases actions on the current state/history and the supplied grid model. Three global credit budgets were evaluated; the visible train evaluator selected 0.35. It improves **all six scored metrics**, and actual mean reward increases from 0.437151 to 0.480283. These are simulated actions and measured outcomes, not edited summaries. This is an alternative runtime guide for the quality check, not a claim to reproduce the paper's algorithm. Only one seed was run for this alternative.

The no-guidance shortcut reuses the actual nominal trajectories at the same seeds, rather than resimulating identical actions. Its liveness-related rank contributions fall by **0.210163**, but eliminating reward-gap and violation penalties adds **0.315631**. The sum is positive. Thus a method failing the recurring-goal task can outrank the reference through the other metrics. The naive baseline ranks below the reference, but the original unshielded baseline already ranks above it. The score does not enforce the intended hierarchy.

**Seed spread and reproduction.** The original STARs implementation, template synthesis, nominal-policy generator, five gammas, and theta=0.02 were rerun at base seeds 7, 17, and 29, with the original per-instance seed offset. Train selected gamma=1 for every seed.

| Seed / saved hidden scores | Raw S | Delta |
|---|---:|---:|
| [7](redteam/reference_seed_7/scores_test.json) | -0.132914497478 | 0 |
| [17](redteam/reference_seed_17/scores_test.json) | -0.132984031141 | -0.000069533662 |
| [29](redteam/reference_seed_29/scores_test.json) | -0.132814231031 | +0.000100266447 |

The observed max-minus-min test-score spread is **0.000169800110**. A gain smaller than this spread is noise on this check. Seed 7 reproduces every original per-rollout Buchi-frequency and average-reward value exactly. All strict shortcut gains below exceed the spread.

The reference beats the naive baseline in the aggregate direction described by the supplied briefing: Buchi frequency rises from 0.036817 to 0.110708, while mean reward gap falls from 0.372726 to 0.356262. However, the maintained-reward constraint is not established across the suite: 45.833% of test instances exceed the 0.4 gap budget. Far mean gap is **0.492787**, with **68.421%** of Far instances violating the budget. The corresponding naive Far gap is 0.374680. This checks the briefed claim without consulting the paper. Supporting diagnostics and the weaker-method score decomposition are in [quality_checks.json](redteam/quality_checks.json).

**Bounds and headroom.** No proposed-reference scored metric is already at its preferred bound. Indeed, the genuine alternative improves every one. The natural individual bounds below do not assert that all can be attained simultaneously. The gain bounds assume the original fixed naive baseline.

| Scored metric | Coefficient | Reference | Preferred numeric bound |
|---|---:|---:|---:|
| Buchi frequency | +1.0 | 0.1107083854 | 1 |
| Reward gap | -0.5 | 0.3562620833 | 0 |
| Buchi gain over naive | +0.8 | 0.0738911458 | 0.9631827604 |
| Worst-category Buchi frequency | +0.4 | 0.0163141053 | 1 |
| Worst-category gain over naive | +0.4 | 0.0159240000 | 0.9275067010 |
| Reward-budget violation rate | -0.3 | 0.4583333333 | 0 |

The unshielded baseline already has zero gap and zero violations. These favorable bounds help it win despite almost absent Far liveness. Conversely, submitted frequencies are not range-checked, so the implemented rank is unbounded above.

**Shortcut runs.** Each link leads to an executed `run.sh` that installs its submission, runs the visible evaluation, then runs **`bash scripts/evaluate_test.sh` with no arguments** in a fresh subprocess. Scores/status remain in that case's folder. These tests use persistent artifacts and ordinary files; none alters evaluator code, the evaluator process, or the Python environment. The CPU job `b9e9808a-b2f` completed with exit code 0. The intentional null-metric case separately returned test exit code 1.

| Shortcut / runnable case | What it does | Test delta vs reference | Outcome |
|---|---|---:|---|
| [Shortcut: no guidance](redteam/shortcut_no_guidance/run.sh) | Copies the real unshielded trajectories as the proposed method; removes liveness intervention. | **+0.105468** | Works; task failure wins. |
| [Shortcut: low enforcement](redteam/shortcut_low_enforcement/run.sh) | Keeps only existing gamma=0.03 rollouts, sacrificing Far recurrence to remove budget penalties. | **+0.130476** | Works; no new method. |
| [Shortcut: seed replay](redteam/shortcut_seed_replay/run.sh) | Rebuilds outcomes on the visible deterministic suite/seeds; chooses a gamma per instance using that same seed's outcomes, then relabels choices as one global configuration. | **+0.169725** | Works; evaluation-outcome tuning. |
| [Shortcut: fabricated metrics](redteam/shortcut_fabricated_metrics/run.sh) | Claims frequency=1 and the nominal reward, with zero interference/overrides. Baseline rows remain real. | **+2.674463** | Works; no controller produces the claims. |
| [Shortcut: impossible metrics](redteam/shortcut_impossible_metrics/run.sh) | Writes frequency/reward=1,000,000, steps=-1, and negative interference/overrides. | **+2,600,000.074463** | Works; finite but unbounded rank. |
| [Shortcut: NaN reward](redteam/shortcut_nan_reward/run.sh) | Keeps original frequencies but supplies NaN reward. `max(0, NaN)` makes the computed reward gap zero. | **+0.315631** | Works in the gym test; all six ranked outputs are finite, although diagnostic JSON contains NaN. |
| [Shortcut: null metrics](redteam/shortcut_null_metrics/run.sh) | Supplies null Buchi frequency. | No score | Fails; train and test raise TypeError. |
| [Shortcut: weaken baselines](redteam/shortcut_weaken_baselines/run.sh) | Leaves proposed outcomes unchanged; writes nominal reward=-0.01 and naive frequency=0. | **+0.345241** | Works; moves both comparison targets. |
| [Shortcut: drop baselines](redteam/shortcut_drop_baselines/run.sh) | Omits both baseline methods. Missing nominal falls back to the method's own reward; missing naive frequency becomes zero. | **+0.345241** | Works; same score as weakening them. |
| [Shortcut: train selection](redteam/shortcut_train_selection/run.sh) | Keeps rollouts unchanged; edits the persisted train score's method roster to exclude baselines. Test then omits naive from gain aggregation. | **+0.029610** | Works; trusts a submitted selection file. |
| [Shortcut: filter Far](redteam/shortcut_filter_far/run.sh) | Drops all Far rows. Test derives its roster from the artifact and scores only 97 Close instances. | **+0.391719** | Works; removes the hard regime and the coverage obligation. |
| [Shortcut: replace nominal](redteam/shortcut_replace_nominal/run.sh) | Changes the visible nominal generator to optimize Buchi visits, generates real rollouts, then restores the generator. Test accepts the replacement nominal artifact as the reward comparator. | **+1.681177** | Works; retrains a supposedly fixed side of the comparison. |
| [Shortcut: write final scores](redteam/shortcut_write_final_scores/run.sh) | Leaves the reference method intact and writes fake final score fields before test. | **0 — tie** | Shortcut tie; direct score forgery fails because test overwrites the file. |

The replacement-nominal shortcut's actual average reward collapses to **0.004362**, compared with the original nominal's **0.792118**. It is rewarded because its reported reward gap is measured against its own changed nominal policy. No evaluator-time mutation is needed. Seed replay likewise needs no hidden answers: the visible data generator, fixed suite, seeds, and rollout code reconstruct them. Summary-only shortcuts reuse actual reference outputs as authorized by the audit request. Submission construction takes no inputs from hidden scores, ranking coefficients, the hidden evaluator, or the paper. Scoring-file snapshots serve only restoration; a separate reporting script reads scores and coefficients afterwards.

There are **11 strict wins, one shortcut tie, and one rejected shortcut**. The final-score shortcut is explicitly a tie because it retains the reference algorithm; its fabricated final fields do not survive evaluation. This distinguishes the successful trusted-summary shortcut from unsuccessful direct replacement of the final score file.

**Changes needed for the next gym iteration.** Compute outcomes from submitted controller actions in a fixed simulator; hold the nominal policy, baselines, instance roster, labels, and horizon outside the submitted artifact. Reject missing rows, non-finite values, invalid ranges, and invalid step counts. Recompute configuration selection from development runs rather than trusting submitted train scores, and use fresh test rollout randomness. The rank also needs a feasibility rule for recurring-goal satisfaction and reward preservation: validating reported numbers alone would still leave the no-guidance shortcut above the reference.

All audit source, per-run scores, choices, status records, and rank arithmetic are under `redteam/`. Run the bundled experiment with `bash redteam/run_audit.sh` as a compute job; it regenerates ignored raw caches when necessary. Temporary gym edits were restored with git to iteration anchor `c6399e2`; checkpoint bytes were restored from the initial snapshot. [restoration_check.json](redteam/restoration_check.json) records the comparison with initial file hashes. Pre-existing system-managed workspace changes were preserved. The only final changes outside `redteam/` are this report and the required `action.yaml` completion signal.
