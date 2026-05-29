# Experiment Overview

## factorybot_buchi_reward_tradeoff

Tests the paper's central FactoryBot claim: a runtime guide should make the robot visit the required recurring-goal region more often while still collecting high reward. The experiment evaluates the tradeoff across both Close and Far gridworld instances, because the distance between reward-seeking behavior and recurring-goal satisfaction changes how difficult the compromise is.

## factorybot_reward_preservation

Tests whether a method's recurring-goal gains come at an acceptable reward cost. This prevents methods from appearing strong by driving directly to the recurring-goal region while abandoning the reward objective that the nominal policy was designed to optimize.

## factorybot_safety_compliance

Tests whether a method maintains the safety side of the specification while pursuing both reward and recurring-goal visits. This is a constraint experiment: a high recurring-goal frequency should not count as success if it is achieved through invalid or unsafe behavior.

## factorybot_vs_naive_baseline

Tests whether the method improves on generic exploratory intervention under matched reward conditions. The purpose is to separate targeted runtime guidance from the simpler effect of adding randomness to the nominal policy.
