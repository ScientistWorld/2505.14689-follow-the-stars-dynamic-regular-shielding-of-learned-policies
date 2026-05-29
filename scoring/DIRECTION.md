# Research Direction

## Research Problem

This benchmark studies runtime guidance for learned probabilistic policies under formal recurring-goal and safety requirements. The central question is whether a method can take an already reward-optimized FactoryBot policy and, without retraining it for the new objective, make executions satisfy required recurring visits while preserving average reward.

## Core Contribution Scope

Future scientists should work on post hoc runtime guidance for finite robot-control MDPs with omega-regular or recurring-goal objectives. The contribution being tested is not a better gridworld policy learner; it is a better way to mediate between an existing policy's action preferences and formal deployment-time obligations.

## Approach Scope

In-bounds approaches may redesign how runtime guidance scores, filters, reweights, samples, or schedules actions using the nominal action distribution, current state, execution history, and formal objective. They may introduce new progress measures, intervention schedules, online adaptation rules, objective-composition logic, or safety-handling mechanisms, as long as the method remains a runtime guide over the existing nominal policy.

Methods may use model information supplied by the benchmark, such as the finite transition graph and formal objective labels, because the FactoryBot setting is explicitly a known finite MDP. They may also tune global hyperparameters on development instances, provided final scoring follows the fixed evaluation protocol.

## Out of Bounds

- Replacing the task with end-to-end policy training on the Buchi objective.
- Reporting a policy that ignores or discards the nominal reward-optimized policy.
- Changing the FactoryBot reward function, grid distribution, safety rules, Buchi-region definitions, or Far/Close split for scored results.
- Optimizing only Buchi frequency while allowing reward collapse or safety violations.
- Switching the benchmark focus to Overcooked-AI, LunarLander, or another environment for the primary score.
- Using evaluation rollouts to tune per-instance behavior after seeing their outcomes.
