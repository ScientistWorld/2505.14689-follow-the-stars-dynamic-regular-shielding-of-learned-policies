# Scientist Constraints

These constraints define what future scientist agents must hold fixed when trying to improve the benchmark scores. They prevent gains that come from changing the benchmark rather than from better runtime guidance.

## Problem Setting

Solve the post-shielding problem: guide the benchmark's pre-existing probabilistic nominal policy at runtime in FactoryBot. The scorers compute the nominal policy themselves; a method may query it (through the `nominal` mapping at each step and `model.nominal(state)`), but may not retrain, replace or edit it. Editing `data/factorybot_nominal.py` changes nothing the scorers use.

## Data and Instances

Develop on the visible 383-grid suite (`data/factorybot_suite.json`, `scripts/evaluate_train.sh`). The held-out test grids and their random numbers exist only in `eval/test/`; methods must not read, import or reconstruct anything from `eval/test/`. New grids may be generated for development with `data/factorybot.py`.

## Evaluation Protocol

The horizon (100,000 steps), random start state, reward function, Büchi cell, reward budgets, Close/Far categories and baselines are fixed by the scorers and cannot be changed by a submission. A guide sees one grid and one budget at a time; the scorer re-imports the guide module for every run, and a guide must not carry information between runs by other means (files, environment, other processes), must not inspect the scorer's process (call stack, globals, random-number state), and must not use outcomes of evaluation runs to choose its behaviour on later runs.

## Allowed Method Inputs

At runtime a guide may use the current state, its own execution history, the observed per-step rewards, the nominal action distribution (at any state), the transition graph, the Büchi cell and the reward budget it is given. Global hyperparameters may be tuned on the visible suite. The reward-cell location, the Close/Far label and the random numbers are not provided and must not be obtained from scorer internals.

## Compliance Checklist

- [ ] The method is submitted as a guide spec in `checkpoints/guides/` and scored by `scripts/evaluate_train.sh` / `scripts/evaluate_test.sh` without arguments.
- [ ] The nominal reward policy is used as provided; it is not retrained or replaced.
- [ ] Nothing under `eval/test/` is read or imported by the method.
- [ ] No state is shared between scoring runs and the scorer process is not inspected.
- [ ] Hyperparameters are global (chosen on the visible suite), not per evaluation grid.
- [ ] Evaluation code does not import from `method/`; the guide is loaded by path from its spec.
