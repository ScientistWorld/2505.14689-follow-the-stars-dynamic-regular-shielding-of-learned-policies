# Paper's Method

## Key Contribution

The paper introduces Strategy-Template-based Adaptive Runtime Shields (STARs), a dynamic post-shielding framework for enforcing omega-regular specifications over learned probabilistic policies. Its distinctive feature is a tunable enforcement parameter, gamma, that controls how strongly the runtime shield biases the policy toward formal obligations.

## Approach

STARs starts from a known finite MDP and an omega-regular objective represented as a parity condition. It computes a winning strategy template for the induced game; the template separates obligations into unsafe actions, co-live actions to eventually avoid, and live action groups that must eventually be taken when their source states recur.

At runtime, STARs takes the nominal policy's action distribution in the current state and modifies it using counters derived from the execution history. Unsafe actions receive zero probability. Co-live actions are downweighted as they are sampled. Live groups are upweighted when their source states are repeatedly visited without taking one of the group's actions. The result is normalized into a shielded action distribution. The enforcement parameter gamma and threshold theta determine how aggressively these probability changes occur and can be changed at runtime.

For changing specifications, STARs relies on compositional strategy templates: newly arriving omega-regular objectives can be integrated into the existing template when the current run remains in the combined winning region. For action failures, unavailable actions can be treated as temporarily or persistently excluded from the template.

## Main Claims

- **Primary claim:** A runtime shield can enforce omega-regular objectives, including liveness, over a pre-computed probabilistic policy while preserving much of the policy's reward performance.
- **FactoryBot empirical claim:** On random gridworld instances, increasing enforcement increases Buchi-region visit frequency, with an explicit tradeoff against average reward, and the proposed shield achieves higher Buchi frequency than a naive exploration-style shield at comparable reward levels.
- **Dynamic-adaptation claim:** The shield can accommodate changing objectives or action availability without retraining the nominal policy, provided the updated objective remains satisfiable from the current setting.
- **Scalability/application claims:** The same framework scales to large finite game graphs in Overcooked-AI and can improve helipad landing rates in a coarse-abstraction LunarLander setting.
