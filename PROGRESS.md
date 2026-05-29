# Progress

## What Works

- FactoryBot-style finite grid MDP suite is generated from fixed seeds in `data/factorybot.py`.
- The STARs runtime shield implements unsafe/co-live/live-group probability modification, counter updates, thresholding, and normalization.
- `scripts/method.sh` runs the proposed method and `scripts/evaluate.sh` scores JSONL rollout artifacts without importing from `method/`.
- A short local smoke test completed and showed STARs increasing Buchi frequency over the unshielded policy and naive exploratory baseline.

## Results

- Local smoke test at 1,000 steps per instance: `apply_stars` Buchi frequency 0.096 versus `apply_naive` 0.017 and `unshielded` 0.000. This is only a smoke test, not the submitted reproduction score.
- Paper reference for the FactoryBot matched-reward comparison is encoded in `scoring/reference.json` from Figure 4b visual estimates: ApplySTARs around 0.24 Buchi frequency at the 0.5 reward-closeness threshold versus ApplyNaive around 0.015.

## Remaining

- Run the full CPU reproduction job with a longer horizon.
- Inspect the job scores and update the milestone to `core_claim` only if the full run supports the claimed tradeoff.
- Optionally add Far/Close split scoring after the core aggregate is confirmed.

## Issues

- The paper does not publish FactoryBot table values; the reference file uses visual estimates from Figure 4b and documents this.
- The reproduction uses a compact fixed suite of six FactoryBot instances rather than the paper's 383 instances to keep the CPU job lightweight.

## Deviations from Paper

- **FactoryBot scale:** The paper evaluates 383 random instances for 100,000 steps each. This reproduction uses six fixed generated instances and submits a 30,000-step CPU run first. The algorithmic procedure is unchanged; only the number of instances and rollout horizon are scaled down.
- **Nominal policy:** The paper starts from an average-reward optimized learned policy. This reproduction uses a stochastic shortest-path reward-seeking policy over the same finite grid MDP setting, preserving the key condition that the nominal policy optimizes reward without the Buchi objective.
