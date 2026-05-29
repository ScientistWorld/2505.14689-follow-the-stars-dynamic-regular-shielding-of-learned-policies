"""Nominal reward-policy generation for FactoryBot.

The paper evaluates STARs as a post-shield over a policy that optimizes the
FactoryBot reward without the Büchi objective. This module provides that
benchmark policy as data/problem code, not as part of the STARs method, so
baselines and future methods can query the same nominal distribution.
"""

from __future__ import annotations

from data.factorybot import ACTIONS, FactoryBotInstance


PolicyTable = dict[tuple[int, int], dict[str, float]]


def optimal_average_reward_policy(
    instance: FactoryBotInstance,
    *,
    epsilon: float = 0.04,
    iterations: int = 500,
    tolerance: float = 1e-10,
) -> PolicyTable:
    """Compute an epsilon-perturbed average-reward optimal policy.

    Relative value iteration solves the deterministic finite MDP's optimal
    average-reward equations. Epsilon perturbation keeps every action possible,
    matching the paper's requirement that STARs can post-process probabilistic
    policies even when the optimal reward policy would be deterministic.
    """

    states = list(instance.states)
    reference = instance.start if instance.start in states else states[0]
    bias = {state: 0.0 for state in states}

    for _ in range(iterations):
        values = {
            state: max(
                instance.reward_value(state, action) + bias[instance.step(state, action)]
                for action in ACTIONS
            )
            for state in states
        }
        reference_value = values[reference]
        updated = {state: values[state] - reference_value for state in states}
        delta = max(abs(updated[state] - bias[state]) for state in states)
        bias = updated
        if delta < tolerance:
            break

    policy: PolicyTable = {}
    for state in states:
        action_values = {
            action: instance.reward_value(state, action) + bias[instance.step(state, action)]
            for action in ACTIONS
        }
        best_value = max(action_values.values())
        greedy = [
            action
            for action, value in action_values.items()
            if abs(value - best_value) <= 1e-9
        ]
        probs = {action: epsilon / len(ACTIONS) for action in ACTIONS}
        for action in greedy:
            probs[action] += (1.0 - epsilon) / len(greedy)
        policy[state] = probs

    return policy
