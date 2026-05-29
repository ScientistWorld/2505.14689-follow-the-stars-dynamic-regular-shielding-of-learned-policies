"""Run non-STAR FactoryBot baselines and write the shared output format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Mapping

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.factorybot import ACTIONS, FactoryBotInstance, read_suite, write_suite
from data.factorybot_nominal import PolicyTable, optimal_average_reward_policy


def total_variation(p: Mapping[str, float], q: Mapping[str, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(float(p.get(k, 0.0)) - float(q.get(k, 0.0))) for k in keys)


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


def run_baseline_episode(
    instance: FactoryBotInstance,
    method: str,
    steps: int,
    nominal_policy: PolicyTable,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    state = rng.choice(list(instance.states))
    visits = 0
    reward_sum = 0.0
    tv_sum = 0.0
    overrides = 0

    for _ in range(steps):
        nominal = nominal_policy[state]
        if method == "apply_naive":
            policy = {a: 0.5 * nominal[a] + 0.5 / len(ACTIONS) for a in ACTIONS}
        elif method == "unshielded":
            policy = nominal
        else:
            raise ValueError(f"unknown baseline {method}")

        tv_sum += total_variation(nominal, policy)
        action = sample_action(policy, rng)
        nominal_action = max(nominal, key=nominal.get)
        if action != nominal_action:
            overrides += 1
        reward_sum += instance.reward_value(state, action)
        state = instance.step(state, action)
        if state == instance.buchi:
            visits += 1

    return {
        "instance": instance.name,
        "category": instance.category,
        "method": method,
        "steps": steps,
        "gamma": None,
        "theta": None,
        "buchi_frequency": visits / steps,
        "average_reward": reward_sum / steps,
        "mean_tv_interference": tv_sum / steps,
        "override_rate": overrides / steps,
        "nominal_policy": "relative_value_iteration_average_reward",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=Path("data/factorybot_suite.json"))
    parser.add_argument("--output", type=Path, default=Path("checkpoints/factorybot_baseline_results.jsonl"))
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--epsilon", type=float, default=0.04)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    if not args.suite.exists():
        write_suite(args.suite)
    instances = read_suite(args.suite)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        for idx, instance in enumerate(instances):
            nominal_policy = optimal_average_reward_policy(instance, epsilon=args.epsilon)
            for method in ("unshielded", "apply_naive"):
                row = run_baseline_episode(instance, method, args.steps, nominal_policy, args.seed + idx)
                f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
