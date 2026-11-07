"""Run actual rollouts in a compute job, preserving original STARs code."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data.factorybot import read_suite
from data.factorybot_nominal import optimal_average_reward_policy
from method.factorybot_method import run_episode
from method.template_synthesis import synthesize_buchi_reach_template
from redteam.better_reward_accounting.method import run_episode as run_better

SEEDS = (7, 17, 29)
GAMMAS = (0.03, 0.1, 0.2, 0.5, 1.0)
BUDGETS = (0.15, 0.25, 0.35)


def worker(task):
    idx, instance, needed_seeds, need_better, steps = task
    nominal = optimal_average_reward_policy(instance, epsilon=0.04)
    template = synthesize_buchi_reach_template(instance, {instance.buchi})
    out = {}
    for seed in needed_seeds:
        rows = [run_episode(instance, name, steps, GAMMAS[0], 0.02,
                            nominal, template, seed + idx)
                for name in ("unshielded", "apply_naive")]
        rows += [run_episode(instance, "apply_stars", steps, gamma, 0.02,
                             nominal, template, seed + idx) for gamma in GAMMAS]
        out[f"reference_seed_{seed}"] = rows
    if need_better:
        out["better_reward_accounting"] = [
            run_better(instance, nominal, steps, 7 + idx, budget) for budget in BUDGETS]
    return instance.name, out


def completed_instances(path, expected):
    if not path.exists():
        return set()
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    counts = {}
    for row in rows:
        counts[row["instance"]] = counts.get(row["instance"], 0) + 1
    complete = {name for name, count in counts.items() if count == expected}
    if len(complete) != len(counts):
        path.write_text("".join(json.dumps(r) + "\n" for r in rows if r["instance"] in complete))
    return complete


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=100000)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    names = [f"reference_seed_{s}" for s in SEEDS] + ["better_reward_accounting"]
    paths = {name: ROOT / "redteam" / name / "rollouts.jsonl" for name in names}
    done = {name: completed_instances(paths[name], 3 if name == "better_reward_accounting" else 7)
            for name in names}
    instances = read_suite(ROOT / "data/factorybot_suite.json")
    tasks = []
    for idx, instance in enumerate(instances):
        seeds = [s for s in SEEDS if instance.name not in done[f"reference_seed_{s}"]]
        need_better = instance.name not in done["better_reward_accounting"]
        if seeds or need_better:
            tasks.append((idx, instance, seeds, need_better, args.steps))
    print(f"Computing {len(tasks)} / {len(instances)} instances with {args.workers} workers", flush=True)
    handles = {}
    try:
        for name in names:
            paths[name].parent.mkdir(parents=True, exist_ok=True)
            handles[name] = paths[name].open("a", buffering=1)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(worker, task) for task in tasks]
            for idx, future in enumerate(as_completed(futures), 1):
                name, outputs = future.result()
                for case, rows in outputs.items():
                    for row in rows:
                        handles[case].write(json.dumps(row) + "\n")
                    handles[case].flush()
                    os.fsync(handles[case].fileno())
                if idx % 5 == 0 or idx == len(tasks):
                    print(f"Saved {idx}/{len(tasks)} completed instances; last={name}", flush=True)
    finally:
        for handle in handles.values():
            handle.close()
    (ROOT / "redteam/compute_protocol.json").write_text(json.dumps({
        "steps": args.steps, "seeds": SEEDS, "gammas": GAMMAS,
        "better_budgets": BUDGETS, "instance_count": len(instances),
        "workers": args.workers, "reference_implementation": "method.factorybot_method.run_episode",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
