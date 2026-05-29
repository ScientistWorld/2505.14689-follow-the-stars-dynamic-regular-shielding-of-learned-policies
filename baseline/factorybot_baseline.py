"""Run non-STAR FactoryBot baselines and write the shared output format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.factorybot import read_suite, write_suite
from method.factorybot_method import run_episode


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
            for method in ("unshielded", "apply_naive"):
                row = run_episode(instance, method, args.steps, 0.002, 0.02, args.epsilon, args.seed + idx)
                f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()

