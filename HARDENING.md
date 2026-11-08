# Hardening report (iteration 11)

**Better results now score higher.** On the hidden test, a genuinely better guide gains **+0.450**. A better STARs variant built from the paper's own dynamic-γ mechanism gains **+0.025**, which is 18× the seed spread and 8.8 paired standard errors. Every weaker variant and every shortcut from `REDTEAM.md` now scores below the reference, scores as failed, or leaves the scores unchanged. The reference algorithm is unchanged: through the new interface it reproduces the old saved rollouts bit-for-bit.

All numbers come from job `4e266a0c-988`: full 100,000-step horizon, 383 visible grids for train, 256 hidden grids for test. Raw results are in `redteam/hardening/out/` (`summary.json`, `test_variants.json`, `train_variants.json`, `tamper_scores_test.json`, `test_noise_alt{1,2}.json`). The rank is Σ coefficient × (metric − reference metric), using the coefficients in `scoring/reference.json`.

## What was wrong and what changed

The old evaluator scored a JSONL file of numbers that the method wrote itself: Büchi frequency, average reward, and both baseline rows. It took the nominal reward comparator, the instance roster and the config selection from files the method controlled. It then ranked a linear mix of frequency, reward gap and violations, in which doing nothing beat the reference.

The fixes, applied together:

1. **The scorer runs the method.** A method is now a *runtime guide*: a factory named in `checkpoints/guides/<name>.json`, returning an object with `act(state, nominal)` and `observe(...)`. `eval/train/` and `eval/test/` load each guide by path, build a fresh one for every (grid, budget) run, check every returned distribution, sample the action themselves, simulate the move, and compute every number. Each run re-imports the guide module and restores `sys.path`, so no module-level state carries over between runs. Guides get a read-only model: the graph, the Büchi cell, and black-box nominal queries. They do not get the reward cell, the Close/Far label or the random numbers.
2. **The scorer fixes everything on the other side of the comparison.** That covers the grids, the simulator and reward, the nominal policy (its own copy of the relative-value-iteration code, not `data/`), the rollout random numbers (paired: every method sees the same start and random stream on a grid), the horizon, the budgets, and both baselines. `unshielded` and `apply_naive` are computed by the scorer and reserved as names; naive uses its best global mixing weight per budget. `eval/train/` and `eval/test/` use only the standard library and share no code with each other, `data/` or `method/`.
3. **Hidden test inputs.** The test runs 256 held-out grids (128 Close / 128 Far, sizes 5–13, same generator as the visible suite) with rollout seeds that exist only in `eval/test/`. Train is the visible 383-grid suite with visible seeds.
4. **Metrics are measured at matched reward, with a hard constraint.** Every guide runs once per reward budget ε ∈ {0.1, 0.2, 0.3, 0.4}. Any run whose average reward falls more than ε below the nominal's, on the same grid and random numbers, counts as zero. This is the paper's Fig. 4b comparison (Büchi frequency at ε-closeness), but violators count as zero instead of being dropped. The scored metrics:

   | Metric | Coefficient | Why |
   |---|---:|---|
   | `matched_reward_buchi_frequency` (primary) | 1.0 | Paper's headline: recurring-goal frequency at matched reward |
   | `matched_reward_gain_over_naive` | 0.5 | Paper's comparative claim against ApplyNaive |
   | `worst_category_matched_reward_buchi_frequency` | 0.5 | Paper stresses that Far grids are much harder; stops a guide winning on Close grids only |
   | `liveness_success_rate` | 0.25 | Per-run success: within budget **and** Büchi frequency ≥ 1/\|Q\| (Thm. 12's attainable level) |

   No metric rewards preserving reward on its own, so a method that fails the liveness task cannot buy rank with reward. The old ungated `buchi_frequency`, `reward_gap_to_nominal` and `reward_budget_violation_rate` are gone from the rank. Gap and violation rate are still reported per budget and per category as diagnostics.
5. **Failure rule.** A crash, a non-mapping return, an unknown action, or probabilities that are negative, non-finite or don't sum to 1 (±1e-6), on any step of any run, scores the method as failed. All frequency and rate metrics become 0 and the gain becomes −naive.
6. **No submitted file is trusted.** The test never reads `scores_train.json`, rollout rows or spec fields beyond `module`, `factory` and `params`. Final scores are always overwritten.

Weights: the single experiment keeps weight 1.0. The coefficients were chosen as above. Frequency and its naive gain together weigh 1.5, the Far-side robustness term 0.5 because the paper emphasises Far grids, and the per-run success rate 0.25 because its 0–1 scale is about 5× larger than the frequencies.

`scoring/reference.json` keeps the paper's Fig. 4b readings unchanged. STARs reads 0.042 / 0.090 / 0.138 / 0.122 and ApplyNaive 0.031 / 0.033 / 0.029 / 0.028 at ε = 0.1–0.4; these are recorded in the description and averaged into the results (STARs 0.098, naive 0.030, gain 0.068). The description also explains how the averaging differs from the paper's.

## Reference before and after

| | Before (old metric) | After (hidden test) | After (train) |
|---|---|---|---|
| Raw rank S | −0.1329 | 0.2039 | 0.2152 |
| Primary metric | Büchi frequency 0.1107 at gap 0.356, 45.8% budget violations | matched-reward frequency 0.0722 | 0.0741 |
| Gain over naive | 0.0739 | 0.0451 | 0.0482 |
| Worst category (Far) | 0.0163 | 0.0039 | 0.0046 |
| Liveness success | — | 0.429 | 0.459 |

The two scales are different metrics and should not be compared directly. The method itself is unchanged: through the new interface the old seed-7 rollouts are reproduced exactly (e.g. `close_5_1000`, γ=0.5: frequency 0.23992, reward 0.75004). What changed is the operating point: one global γ per budget, picked on the visible suite from the paper's γ grid {1e-3, 1e-2, 0.05, 0.1, 0.2, 0.5, 1} with θ = 0.02. The picks were γ = 0.01 / 0.2 / 1 / 1 for ε = 0.1 / 0.2 / 0.3 / 0.4.

**The paper's claim holds in the paper's direction** on the hidden test, at every budget:

| ε | STARs (matched freq) | naive (best mix) | unshielded |
|---|---:|---:|---:|
| 0.1 | 0.0315 | 0.0219 | 0.0171 |
| 0.2 | 0.0664 | 0.0267 | 0.0171 |
| 0.3 | 0.0950 | 0.0267 | 0.0171 |
| 0.4 | 0.0960 | 0.0333 | 0.0171 |

Among runs within budget (the paper's own averaging), STARs reaches 0.122 at ε = 0.2 and 0.177 at ε = 0.4, against the paper's 0.090 and 0.122. The γ sweep reproduces Fig. 4a's trends (visible suite, 100k steps): as γ goes 1e-3 → 1, Close frequency rises 0.036 → 0.209 with the reward gap rising −0.005 → 0.207, and Far frequency rises 4.8e-7 → 0.018 with the gap rising 0.001 → 0.480. Far is much steeper on reward, as the paper reports.

## Do better results score higher? (variants, hidden test)

| Variant | Before Δ | After Δ (test) | After Δ (train) | Paired z (test) |
|---|---:|---:|---:|---:|
| `credit_tour`: genuinely better guide (iteration-10 red-team reward-credit tours, ported to the interface) | +0.884 | **+0.450** | +0.433 | 25.5 |
| `stars_dynamic`: same template and Def. 2 shield, γ switched at runtime between 1 and 0 to hold the budget (paper Rem. 11) | — | **+0.025** | +0.023 | 8.8 |
| reference `apply_stars` | 0 | 0 | 0 | — |
| `low_enforcement`: fixed γ = 0.03 | +0.130 | **−0.041** | −0.048 | −6.4 |
| `apply_naive` (scorer baseline) | −0.176 | **−0.081** | −0.088 | −12.1 |
| `no_guidance` / `unshielded` | +0.105 | **−0.162** | −0.184 | −12.0 |

**Seed noise.** I reran the reference and the baselines on the hidden grids under two alternative rollout random streams. The rank spread is 0.0014 (S = 0.2039 / 0.2035 / 0.2049). The STARs − naive effect (0.0451 / 0.0450 / 0.0451) is about 30× the spread. The smallest genuine improvement, `stars_dynamic` at +0.025, is 18× the spread. Paired standard errors over the 256 hidden grids are 0.003–0.016.

Train and test agree for honest methods. The reference scores 0.215 on train and 0.204 on test; the two better variants gain the same amount on both.

## Shortcuts: fix and score before and after (hidden test)

| Old shortcut | Fix | Before Δ | After |
|---|---|---:|---|
| No guidance | Liveness-gated metrics; reward preservation alone earns nothing | +0.105 | −0.162 |
| Low enforcement | Same | +0.130 | −0.041 |
| Seed replay (per-instance γ from visible outcomes) | Hidden grids and seeds | +0.170 | **0.000 on test** (it gains +0.039 on train and nothing on unseen grids) |
| Fabricated metrics | Scorer computes all numbers; method rows are never read | +2.674 | 0.000 (ignored; identical scores) |
| Impossible metrics | Same, plus invalid distributions fail the run | +2.6e6 | rows ignored; unnormalized output → **failed**, −0.217 |
| NaN reward | Distribution check | +0.316 | NaN output → **failed**, −0.217 |
| Null metrics | Same | crashed the scorer | **failed**, −0.217 (scorer completes) |
| Weaken baselines | Baselines computed by the scorer; reserved names rejected | +0.345 | 0.000 (baseline scores identical) |
| Drop baselines | Same | +0.345 | 0.000 |
| Train selection | Test never reads `scores_train.json` | +0.030 | 0.000 |
| Filter Far | Scorer owns the grid roster; crashes fail the method | +0.392 | spec-side instance filter ignored (0.000); refusing Far grids → **failed**, −0.217 |
| Replace nominal | Scorer computes its own nominal; editing `data/` has no effect | +1.681 | 0.000; a guide that drops the nominal and chases the Büchi cell scores −0.202 (reward collapses, runs zeroed) |
| Write final scores | Overwritten | 0 (tie) | 0.000 |
| Unknown action ("teleport") | New check | — | **failed**, −0.217 |

The file-level shortcuts were all planted at once (`redteam/hardening/tamper.sh`) before running `bash scripts/evaluate_test.sh` with no arguments. The planted files were forged `scores_test.json` and `scores_train.json`, fabricated / impossible / NaN / weakened-baseline / Close-only rows, a Büchi-seeking `data/factorybot_nominal.py`, `apply_naive.json` and `unshielded.json` specs, and an instance filter plus fake metrics inside the reference spec. The reference and both baselines came out **exactly identical** to the clean run (rank Δ 0.0), and both reserved-name specs were rejected.

## Shortcuts left open, and why

- **In-process inspection.** The guide runs inside the scorer process, so malicious code could inspect the call stack or globals (random-number state, simulator tables) or leave files on disk to pass state between runs. Re-importing per run and restoring `sys.path` stop accidental cross-run state; deliberate introspection is forbidden in `CONSTRAINTS.md` and left to the separate grader. A subprocess sandbox per run would cost far more than the scoring itself.
- **Planning around the nominal.** Guides may query the nominal at any state and observe rewards, so they can find the reward cell and plan tours. `credit_tour` does exactly that, and it is treated as an honest stronger method. A guide that rebuilds reward-seeking entirely by itself while ignoring the nominal is out of bounds by the rules but is not detected mechanically. Interference (total variation, override rate) is reported, not scored.
- **Sharpening.** Removing the nominal's 4% exploration raises reward above the nominal (STARs' own θ = 0.02 threshold already does this), and the slack can be spent on Büchi visits. This is a legitimate runtime modification and is left in scope.
- **Test-seed secrecy.** It depends on `eval/test/` being hidden from future agents, as the gym protocol specifies.

## Headroom check

The reference sits at the bound of no scored metric. The bounds are 1 for the frequencies and 1 for the success rate; the reference has 0.072, 0.0039 (worst category) and 0.429. The headroom is where the paper's method falls short:

- **Far grids.** The reference reaches 0.0039 matched frequency and `credit_tour` reaches 0.188.
- **Tight budgets.** At ε = 0.1 the reference gets 0.032; `credit_tour` gets 0.068 and `stars_dynamic` 0.058.

The new design adds these where-it-falls-short measurements: four budgets including the tight 0.1/0.2, per-run zeroing, the worst-category term at matched reward, and per-grid liveness success. A simple variant does not reach any bound: `low_enforcement` and naive score below the reference, and the best variant reaches 0.227 / 0.188 / 0.935.

## What I could not fix

- **Far-grid magnitude.** STARs' Far-grid Büchi frequency stays far below the paper's Fig. 4a (γ = 1: 0.018 here vs ≈0.3 in the paper). The live-group counters reset whenever progress is made. Against a sharp nominal (97% greedy) and θ = 0.02, crossing many attractor layers therefore takes exponentially long, which matches the paper's own K^{n−1} bound in Thm. 11. The paper does not state its θ or its nominal policy's sharpness. I kept the reproduction's setup rather than tune it toward the paper's figure. Directions still hold everywhere, but the reference's Far score is small; that is the headroom the worst-category metric exposes.
- **Primary metric vs the paper's value.** The reference's matched frequency (0.072) is below the paper's mean (0.098) partly because violators count as zero here. Within-budget means are comparable to or above the paper's.
- **Secondary claims** (dynamic objectives, Overcooked-AI scale, LunarLander) remain unreproduced, as before.
- The iteration-10 audit scripts (`redteam/case.py`, `redteam/compute.py`, …) target the retired self-reported JSONL interface and no longer run against the hardened scorer. Their results are kept as history. The current audit is `redteam/hardening/run_hardening.sh`.
