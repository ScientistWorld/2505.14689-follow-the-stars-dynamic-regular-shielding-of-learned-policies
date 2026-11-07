# Experiment Overview

## factorybot_buchi_reward_tradeoff

Tests the paper's central FactoryBot claim: a runtime guide over a fixed reward-seeking policy can make the robot visit the required recurring-goal cell much more often than the policy does on its own, and more often than untargeted extra exploration, while keeping the reward it collects close to the policy's.

The comparison is made at matched reward: each guide is run once per reward budget (0.1, 0.2, 0.3, 0.4 below the unmodified policy's average reward on the same grid and random numbers), and a run that exceeds its budget earns nothing. Averaging over budgets measures the whole reward/liveness tradeoff curve rather than one operating point. Close and Far grids are scored separately as well as together, because when the reward is far from the recurring goal the compromise is much harder; the worst category is scored so that a guide cannot win on easy grids alone. A per-run success rate checks that the recurring goal is actually met at a meaningful rate within budget on individual grids, not only on average.

The scorer owns everything on the other side of the comparison: the held-out grids and random numbers, the simulator, the nominal policy, both baselines and their operating points, the budgets and horizon. It runs the submitted guide itself and recomputes every number; a guide that produces an invalid action distribution or crashes is scored as failed.
