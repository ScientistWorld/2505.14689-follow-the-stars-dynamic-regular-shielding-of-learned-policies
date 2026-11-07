"""Actual rollouts for a fixed nominal policy, with cached transition tables.

Used by the fixed-artifact shortcut. Caching changes arithmetic bookkeeping,
not actions, rewards, initial-state sampling, or rollout horizon.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data.factorybot import ACTIONS, read_suite
from data.factorybot_nominal import optimal_average_reward_policy


def worker(task):
    idx, inst = task
    nominal = optimal_average_reward_policy(inst)
    states = list(inst.states)
    indices = {s: i for i, s in enumerate(states)}
    transitions = [[indices[inst.step(s, a)] for a in ACTIONS] for s in states]
    buchi, reward = indices[inst.buchi], indices[inst.reward]
    best = [max(range(4), key=lambda k: nominal[s][ACTIONS[k]]) for s in states]
    out = []
    for method in ("unshielded", "apply_naive"):
        policies = [[nominal[s][a] if method == "unshielded" else
                     0.5 * nominal[s][a] + 0.125 for a in ACTIONS] for s in states]
        cdfs = [[p[0], p[0] + p[1], p[0] + p[1] + p[2]] for p in policies]
        tvs = [0.5 * sum(abs(nominal[s][a] - policies[i][k])
                        for k, a in enumerate(ACTIONS)) for i, s in enumerate(states)]
        rng = random.Random(7 + idx)
        state = rng.choice(range(len(states)))
        visits = hits = overrides = 0
        tv_sum = 0.0
        for _ in range(100000):
            x = rng.random()
            c0, c1, c2 = cdfs[state]
            action = 0 if x <= c0 else 1 if x <= c1 else 2 if x <= c2 else 3
            overrides += action != best[state]
            tv_sum += tvs[state]
            state = transitions[state][action]
            visits += state == buchi
            hits += state == reward
        out.append({
            "instance": inst.name, "category": inst.category, "method": method,
            "steps": 100000, "gamma": None, "theta": None,
            "buchi_frequency": visits / 100000,
            "average_reward": hits / 100000 - 0.01,
            "mean_tv_interference": tv_sum / 100000,
            "override_rate": overrides / 100000,
            "nominal_policy": "shortcut_replaced_nominal",
        })
    proposed = dict(out[0], method="apply_stars", config="shortcut_replaced_nominal")
    out.append(proposed)
    return out


def main():
    output = Path(sys.argv[1])
    instances = read_suite(ROOT / "data/factorybot_suite.json")
    with output.open("w", buffering=1) as handle, ProcessPoolExecutor(max_workers=4) as pool:
        for idx, rows in enumerate(pool.map(worker, enumerate(instances))):
            for row in rows:
                handle.write(json.dumps(row) + "\n")
            if idx % 50 == 0:
                print(f"Fixed-artifact shortcut saved {idx + 1}/{len(instances)}", flush=True)


if __name__ == "__main__":
    main()
