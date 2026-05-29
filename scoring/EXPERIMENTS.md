# Experiment Overview

## factorybot_buchi_reward_tradeoff

Tests the paper's central FactoryBot claim: a runtime guide should make the robot visit the required recurring-goal region more often while still collecting high reward. The experiment evaluates the tradeoff across both Close and Far gridworld instances, because the distance between reward-seeking behavior and recurring-goal satisfaction changes how difficult the compromise is.

The scored result uses the best global enforcement setting that stays within the configured reward-gap budget to the nominal reward policy. The score also records the worst Close/Far category result and the fraction of instances that exceed the reward-gap budget, so methods cannot hide liveness failures or reward collapse in an overall mean. Close/Far diagnostics are emitted in `scores.json` under `_diagnostics` for analysis.
