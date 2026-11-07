# Problem Definition

## Research Question

How can an already learned probabilistic policy for a finite robot-control environment be guided at runtime so that it satisfies recurring-goal (liveness) requirements while preserving the policy's original reward-seeking behavior?

The FactoryBot-centered benchmark asks this question in gridworlds where the nominal policy is computed to maximize average reward without the recurring-goal objective. At evaluation time, the robot must still collect reward but must also repeatedly visit a designated Büchi cell. A method is a post-processing **runtime guide**: at each step it sees the current state, its own execution history, the nominal action distribution, and the known transition graph with the Büchi cell, and it returns the action distribution to execute. It may not retrain or replace the nominal policy, and it is not told where the reward is.

## Why It Matters

Autonomous systems often receive new correctness requirements after a policy has already been trained. Requiring full retraining for every new liveness goal, obstacle, or deployment constraint is expensive and brittle. A good runtime guide would let engineers update formal obligations while reusing the existing policy.

## Success Criteria

A successful guide should:

- Increase how often the robot visits the required Büchi cell.
- Keep the average reward within a prescribed budget of what the unmodified nominal policy earns on the same grid — at several budgets, from tight (0.1) to loose (0.4).
- Achieve this on both Close grids (reward near the Büchi cell) and Far grids (reward far from it), where the compromise is much harder.
- Visit the Büchi cell at a meaningful rate on as many grids as possible, not only on average.
- Work from information available at runtime; it must not depend on knowing the evaluation grids or random numbers in advance.
