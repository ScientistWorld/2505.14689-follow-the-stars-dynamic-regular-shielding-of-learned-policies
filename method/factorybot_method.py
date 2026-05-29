"""Run ApplySTARs on FactoryBot-style grid instances."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.factorybot import ACTIONS, FactoryBotInstance, read_suite, shortest_distances, write_suite
from method.stars import StarShield, StrategyTemplate, total_variation


def soft_nominal_policy(
    instance: FactoryBotInstance,
    state: tuple[int, int],
    epsilon: float,
    reward_dist: dict[tuple[int, int], int],
) -> dict[str, float]:
    """Reward-seeking stochastic policy, independent of the Buchi objective."""
    best = min(reward_dist.get(instance.step(state, a), 10**6) for a in ACTIONS)
    greedy = [a for a in ACTIONS if reward_dist.get(instance.step(state, a), 10**6) == best]
    probs = {a: epsilon / len(ACTIONS) for a in ACTIONS}
    for a in greedy:
        probs[a] += (1.0 - epsilon) / len(greedy)
    return probs


def buchi_template(instance: FactoryBotInstance) -> StrategyTemplate:
    """Construct the Büchi live-group template used by STARs.

    For a reach-infinitely-often objective on a strongly connected grid, the
    distance layers to the Büchi cell form the live groups: each group contains
    edges from layer i to layer i-1. Repeatedly taking these groups guarantees
    visits to the Büchi cell.
    """
    dist = shortest_distances(instance, instance.buchi)
    max_d = max(dist.values())
    groups = []
    for d in range(1, max_d + 1):
        edges = []
        for state, state_d in dist.items():
            if state_d != d:
                continue
            for action in ACTIONS:
                if dist.get(instance.step(state, action), 10**6) < d:
                    edges.append((state, action))
        if edges:
            groups.append(frozenset(edges))
    return StrategyTemplate(live_groups=tuple(groups))


def sample_action(probs: dict[str, float], rng: random.Random) -> str:
    x = rng.random()
    acc = 0.0
    last = next(iter(probs))
    for action, prob in probs.items():
        acc += prob
        last = action
        if x <= acc:
            return action
    return last


def run_episode(
    instance: FactoryBotInstance,
    method: str,
    steps: int,
    gamma: float,
    theta: float,
    epsilon: float,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    state = instance.start
    shield = StarShield(buchi_template(instance), gamma=gamma, theta=theta)
    reward_dist = shortest_distances(instance, instance.reward)
    visits = 0
    reward_sum = 0.0
    tv_sum = 0.0
    overrides = 0

    for _ in range(steps):
        nominal = soft_nominal_policy(instance, state, epsilon=epsilon, reward_dist=reward_dist)
        if method == "apply_stars":
            policy = shield.distribution(state, nominal, ACTIONS)
        elif method == "apply_naive":
            # The paper's naive baseline perturbs/explores all actions rather
            # than targeting the live template obligations.
            policy = {a: 0.5 * nominal[a] + 0.5 / len(ACTIONS) for a in ACTIONS}
        elif method == "unshielded":
            policy = nominal
        else:
            raise ValueError(f"unknown method {method}")

        tv_sum += total_variation(nominal, policy)
        action = sample_action(policy, rng)
        nominal_action = max(nominal, key=nominal.get)
        if action != nominal_action:
            overrides += 1
        if method == "apply_stars":
            shield.observe(state, action)
        reward_sum += instance.reward_value(state, action)
        state = instance.step(state, action)
        if state == instance.buchi:
            visits += 1

    return {
        "instance": instance.name,
        "category": instance.category,
        "method": method,
        "steps": steps,
        "gamma": gamma if method == "apply_stars" else None,
        "theta": theta if method == "apply_stars" else None,
        "buchi_frequency": visits / steps,
        "average_reward": reward_sum / steps,
        "mean_tv_interference": tv_sum / steps,
        "override_rate": overrides / steps,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=Path("data/factorybot_suite.json"))
    parser.add_argument("--output", type=Path, default=Path("checkpoints/factorybot_results.jsonl"))
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--gamma", type=float, nargs="+", default=[0.03, 0.1, 0.2, 0.5, 1.0])
    parser.add_argument("--theta", type=float, default=0.02)
    parser.add_argument("--epsilon", type=float, default=0.04)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    if not args.suite.exists():
        write_suite(args.suite)
    instances = read_suite(args.suite)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        for inst_idx, instance in enumerate(instances):
            for method in ("unshielded", "apply_naive"):
                row = run_episode(instance, method, args.steps, args.gamma[0], args.theta, args.epsilon, args.seed + inst_idx)
                f.write(json.dumps(row) + "\n")
            for gamma in args.gamma:
                row = run_episode(instance, "apply_stars", args.steps, gamma, args.theta, args.epsilon, args.seed + inst_idx)
                f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
