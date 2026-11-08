# Follow the STARs: Dynamic $ω$-Regular Shielding of Learned Policies

<!-- scope-note -->
> [!NOTE]
> **Not a full reproduction of the paper.** This environment keeps the paper's core problem at a reduced scale so it is easy to run. It measures an AI scientist's idea and how well it is carried out, not the full research loop.

<!-- hardening-note -->
> [!NOTE]
> **Red-teamed and hardened.** A red team tried to score on this environment's hidden test without doing better research, and the environment was then fixed against the shortcuts that worked: see [`REDTEAM.md`](REDTEAM.md) and [`HARDENING.md`](HARDENING.md). The environment as it was before is kept as branch [`pre-hardening`](../../tree/pre-hardening). The runs listed below were made on that earlier version.

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2505.14689"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2505.14689-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| **Paper ID** | [2505.14689](https://arxiv.org/abs/2505.14689) |
|:---|:---|
| **Domain** | Formal methods for reinforcement learning / runtime shielding |
| **TL;DR** | The paper studies how to enforce omega-regular correctness obligations over an already learned probabilistic policy while preserving as much reward-seeking behavior as possible. |

## Summary

The paper addresses runtime shielding for learned autonomous agents when the required specification includes liveness, not only safety. Its central setting is a black-box nominal policy that already optimizes a task reward, plus a separate runtime monitor/controller that must keep executions compliant with formal objectives as deployment conditions change. The FactoryBot benchmark is the most reproducible core setting: a robot moves in random gridworlds, seeks high average reward, and must repeatedly visit a specified Buchi region under static or changing constraints. The headline empirical claim is that the shield can raise Buchi-visit frequency while retaining reward better than a naive stochastic exploration baseline.

## Problem

How can an already learned probabilistic policy for a finite robot-control environment be guided at runtime so that it satisfies safety and recurring-goal requirements while preserving the policy's original reward-seeking behavior?

The FactoryBot-centered benchmark asks this question in gridworlds where the nominal policy is trained or computed to maximize average reward without the recurring-goal objective. At evaluation time, the agent must still collect high reward but must also repeatedly visit a designated Buchi region and respect any safety constraints. A future method should be evaluated as a post-processing runtime guide: it may observe the current state/history and the nominal action distribution, but it should not retrain the nominal policy for the new objective during evaluation.

## The paper's method

The paper introduces Strategy-Template-based Adaptive Runtime Shields (STARs), a dynamic post-shielding framework for enforcing omega-regular specifications over learned probabilistic policies. Its distinctive feature is a tunable enforcement parameter, gamma, that controls how strongly the runtime shield biases the policy toward formal obligations.

## Key results of the paper

- FactoryBot uses 383 random square-grid instances, split into 189 Far and 194 Close instances according to the distance between the reward region and the Buchi region.
- Each FactoryBot instance is evaluated over 100,000 steps from a random initial state, reporting Buchi-region visit frequency and average reward.
- The paper also reports secondary evidence on Overcooked-AI scalability and LunarLander performance, including 87% helipad landings over 200 LunarLander seeds for the liveness shielded policy.

## Leaderboard

FNI of AI scientists on this paper, grader-verified. 0 matches the paper's method, higher is better.

| Model | Innovate |
|---|---:|
| `gpt-5.6-sol-xhigh` | +166.4 |
| `gpt-5.5-xhigh` | +17.9 |
| `gpt-5.6-terra-xhigh` | +15.7 |
| `gpt-5.6-luna-xhigh` | +2.6 |

`innovate`: the model designs its own method. `improve`: it starts from the paper's method.

## Run it

```bash
pip install sciworld
sw research 2505.14689 --mode innovate --agent claude-code
sw evaluate 2505.14689
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

