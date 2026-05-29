# Overview

- **Paper ID:** 2505.14689
- **Title:** Follow the STARs: Dynamic omega-Regular Shielding of Learned Probabilistic Policies
- **Domain:** Formal methods for reinforcement learning / runtime shielding
- **TL;DR:** The paper studies how to enforce omega-regular correctness obligations over an already learned probabilistic policy while preserving as much reward-seeking behavior as possible.

## Short Summary

The paper addresses runtime shielding for learned autonomous agents when the required specification includes liveness, not only safety. Its central setting is a black-box nominal policy that already optimizes a task reward, plus a separate runtime monitor/controller that must keep executions compliant with formal objectives as deployment conditions change. The FactoryBot benchmark is the most reproducible core setting: a robot moves in random gridworlds, seeks high average reward, and must repeatedly visit a specified Buchi region under static or changing constraints. The headline empirical claim is that the shield can raise Buchi-visit frequency while retaining reward better than a naive stochastic exploration baseline.

## Key Results

- FactoryBot uses 383 random square-grid instances, split into 189 Far and 194 Close instances according to the distance between the reward region and the Buchi region.
- Each FactoryBot instance is evaluated over 100,000 steps from a random initial state, reporting Buchi-region visit frequency and average reward.
- The paper also reports secondary evidence on Overcooked-AI scalability and LunarLander performance, including 87% helipad landings over 200 LunarLander seeds for the liveness shielded policy.
