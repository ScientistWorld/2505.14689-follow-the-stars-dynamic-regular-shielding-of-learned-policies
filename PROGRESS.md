# Progress

## What Works

- FactoryBot-style finite grid MDP suite is generated from fixed seeds in `data/factorybot.py`.
- The STARs runtime shield implements unsafe/co-live/live-group probability modification, counter updates, thresholding, and normalization.
- `scripts/method.sh` runs the proposed method and `scripts/evaluate.sh` scores JSONL rollout artifacts without importing from `method/`.
- A short local smoke test completed and showed STARs increasing Buchi frequency over the unshielded policy and naive exploratory baseline.
- A compute job completed successfully at 30,000 steps per instance and supports the core FactoryBot claim.
- A second compute job completed successfully at 100,000 steps per instance, matching the paper's FactoryBot rollout horizon.
- The next submitted job regenerates a broader 30-instance suite across grid sizes 5, 7, 9, 11, and 13, preserving the paper's Close/Far split.

## Results

- Local smoke test at 1,000 steps per instance: `apply_stars` Buchi frequency 0.096 versus `apply_naive` 0.017 and `unshielded` 0.000. This is only a smoke test, not the submitted reproduction score.
- Compute job `1c20f5bd-cc6` at 30,000 steps per instance:
  - `apply_stars`: Buchi frequency 0.1285, average reward 0.5144, Buchi gain over naive 0.1113.
  - `apply_naive`: Buchi frequency 0.0172, average reward 0.4379.
  - `unshielded`: Buchi frequency 0.00024, average reward 0.8019.
- Compute job `d7063bb7-83f` at 100,000 steps per instance:
  - `apply_stars`: Buchi frequency 0.12894, average reward 0.51375, Buchi gain over naive 0.11132.
  - `apply_naive`: Buchi frequency 0.01762, average reward 0.43681.
  - `unshielded`: Buchi frequency 0.00025, average reward 0.80201.
- Paper reference for the FactoryBot matched-reward comparison is encoded in `scoring/reference.json` from Figure 4b visual estimates: ApplySTARs around 0.24 Buchi frequency at the 0.5 reward-closeness threshold versus ApplyNaive around 0.015.

## Remaining

- Higher milestones would require completing the broader FactoryBot run, adding explicit Far/Close scoring, and reproducing Overcooked-AI or LunarLander. The current environment is complete for the core aggregate FactoryBot claim.

## Issues

- The paper does not publish FactoryBot table values; the reference file uses visual estimates from Figure 4b and documents this.
- The completed core reproduction uses a compact fixed suite of six FactoryBot instances rather than the paper's 383 instances. The next job expands this to 30 fixed instances while keeping the 100,000-step horizon.
- On the compact suite, the best aggregate STARs setting is driven mostly by close instances; far instances remain harder, consistent with the paper's discussion that larger reward-to-Buchi distance requires a stronger reward/frequency tradeoff.

## Deviations from Paper

- **FactoryBot scale:** The paper evaluates 383 random instances for 100,000 steps each. The completed core claim uses six fixed generated instances; the next job expands this to 30 instances. The algorithmic procedure is unchanged; only the number of instances is scaled down.
- **Nominal policy:** The paper starts from an average-reward optimized learned policy. This reproduction uses a stochastic shortest-path reward-seeking policy over the same finite grid MDP setting, preserving the key condition that the nominal policy optimizes reward without the Buchi objective.
