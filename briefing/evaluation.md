# Evaluation

## What is measured

A submitted method is a **runtime guide**: at every step it receives the current state and the nominal policy's action distribution and returns the action distribution to execute. The scorer runs the guide itself, inside its own simulator, with its own nominal policy and its own random numbers, and computes every number from the resulting trajectories. Nothing a method writes (rollout rows, metrics, score files, baseline rows, instance lists) is read.

Each guide is run on every grid once per **reward budget** eps in {0.1, 0.2, 0.3, 0.4}, for 100,000 steps from a random start state. The unshielded nominal policy is run on the same grid with the same random numbers; its average reward is the comparator. A run *meets the budget* when its average reward is at most eps below the nominal's.

## Scored metrics

- **`matched_reward_buchi_frequency`** (coefficient 1.0, primary): mean over budgets and grids of the run's Büchi-region visit frequency (fraction of steps that end in the Büchi cell), counted as 0 for runs that miss the budget.
- **`matched_reward_gain_over_naive`** (0.5): the above minus the naive baseline's value.
- **`worst_category_matched_reward_buchi_frequency`** (0.5): the lower of the Close-grid and Far-grid values of the primary metric.
- **`liveness_success_rate`** (0.25): fraction of (grid, budget) runs that meet the budget *and* visit the Büchi region with frequency at least 1/|Q|, where |Q| is the grid's number of free cells.

The rank of a method is the sum over these metrics of coefficient times (method value − reference value). Reward preservation is a hard per-run constraint inside every metric: a run that loses too much reward contributes nothing, so no metric rewards doing nothing or rewards breaking the budget.

**Failure rule.** If a guide raises an exception, returns something that is not a mapping, names an unknown action, or returns probabilities that are negative, non-finite, or do not sum to 1 (tolerance 1e-6) on any step of any run, the method is scored as failed: every frequency/rate metric is 0 and the gain is minus the naive baseline's value.

Diagnostics (per budget and per Close/Far category): budget-violation rate, mean reward gap, ungated Büchi frequency, Büchi frequency among runs within budget (the paper's Fig. 4b averaging), average reward, total-variation distance to the nominal, and override rate.

## Baselines (computed by the scorer)

- **`unshielded`**: the nominal policy unchanged.
- **`apply_naive`**: untargeted extra exploration — the nominal mixed with the uniform distribution. For each budget the scorer uses the best global mixing weight from {0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0} on the scored grids (the strongest such baseline).

## Environment

- Square grids of size 5–13 with 12% walls (free cells connected), one Büchi cell and one reward cell. **Close** grids place the reward at l1-distance 0.1–0.2 × size from the Büchi cell, **Far** grids at 0.7–0.9 × size.
- Actions up/down/left/right move deterministically; moving into a wall or the boundary leaves the robot in place.
- Reward: +1 for a move that enters the reward cell, −0.01 every step.
- Nominal policy: average-reward optimal for the reward alone (relative value iteration), with 4% of probability spread uniformly over all actions.

## Submitting a guide

Write `checkpoints/guides/<name>.json`:

```json
{"name": "my_guide", "module": "path/to/guide.py", "factory": "make_guide", "params": {}}
```

`module` is relative to the workspace root. For every (grid, budget) run the scorer imports the module afresh (no module state survives between runs) and calls `factory(model, budget, params)`, which returns an object with:

- `act(state, nominal) -> {action: probability}` — `nominal` is a read-only mapping of the nominal distribution at `state`.
- `observe(state, action, next_state, reward)` — called after the scorer samples the action and simulates the move.

`model` exposes `size`, `walls`, `states`, `actions`, `buchi` (frozenset of cells), `successor(state, action)` and `nominal(state)`. The reward cell, the Close/Far label and the random numbers are not exposed. The names `unshielded` and `apply_naive` are reserved.

## Train and test

- `bash scripts/evaluate_train.sh` (and `scripts/evaluate.sh`) score every spec in `checkpoints/guides/` on the visible suite: the 383 grids of `data/factorybot_suite.json` (194 Close, 189 Far) with visible rollout seeds. Write `scoring/scores_train.json` / `scoring/scores.json`.
- `bash scripts/evaluate_test.sh` (no arguments) scores every spec on 256 held-out grids (128 Close, 128 Far) from the same generator, with held-out rollout seeds, and writes `scoring/scores_test.json`.
- `data/factorybot_rollout.py` reproduces the rollout protocol for development (`GuideModel`, `rollout_guide`, `rollout_policy`).

A full scoring pass costs roughly 4 × (number of grids) × 100,000 guide calls per method; it runs on CPU and uses all available cores.
