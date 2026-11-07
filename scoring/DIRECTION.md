# Research Direction

## Research Problem

This benchmark studies runtime guidance for learned probabilistic policies under formal recurring-goal requirements. The central question is whether a method can take an already reward-optimized FactoryBot policy and, without retraining it, make executions visit a required cell recurrently while keeping the reward within a prescribed budget of the policy's own.

## Core Contribution Scope

Future scientists should work on post hoc runtime guidance for finite robot-control MDPs with omega-regular or recurring-goal objectives. The contribution being tested is not a better gridworld policy learner; it is a better way to mediate between an existing policy's action preferences and deployment-time obligations, across a range of reward budgets and on both easy (Close) and hard (Far) grids.

## Approach Scope

In-bounds approaches may redesign how runtime guidance scores, filters, reweights, samples, or schedules actions using the nominal action distribution, current state, execution history, observed rewards, the known transition graph and the Büchi cell. They may introduce new progress measures, intervention schedules, online adaptation of enforcement strength to the budget, or composition logic, as long as the method remains a runtime guide over the existing nominal policy. Global hyperparameters may be tuned on the visible suite.

## Out of Bounds

- End-to-end policy training on the Büchi objective that replaces the nominal policy.
- A guide that ignores or discards the nominal reward-optimized policy.
- Changing the FactoryBot reward, grid distribution, Büchi cell, budgets, horizon, baselines, or Close/Far split for scored results (the scorers own all of these).
- Reading or reconstructing the held-out grids or random numbers in `eval/test/`, inspecting the scorer process, or carrying information between scoring runs.
- Switching the benchmark focus to Overcooked-AI, LunarLander, or another environment for the primary score.
