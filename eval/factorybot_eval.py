"""Evaluate FactoryBot shielding outputs without importing method code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def aggregate(rows: list[dict]) -> dict[str, dict[str, float]]:
    by_method: dict[str, list[dict]] = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)

    naive_freq = mean(x["buchi_frequency"] for x in by_method.get("apply_naive", [])) if "apply_naive" in by_method else 0.0
    out = {}
    for method, items in by_method.items():
        out[method] = {
            "buchi_frequency": mean(x["buchi_frequency"] for x in items),
            "average_reward": mean(x["average_reward"] for x in items),
            "mean_tv_interference": mean(x["mean_tv_interference"] for x in items),
            "override_rate": mean(x["override_rate"] for x in items),
            "buchi_frequency_gain_over_naive": mean(x["buchi_frequency"] for x in items) - naive_freq,
        }
    return out


def best_stars_by_reward(rows: list[dict], reward_floor: float | None = None) -> list[dict]:
    stars = [r for r in rows if r["method"] == "apply_stars"]
    if not stars:
        return []
    if reward_floor is None:
        naive = [r for r in rows if r["method"] == "apply_naive"]
        reward_floor = mean(r["average_reward"] for r in naive) - 0.05 if naive else None
    candidates = stars if reward_floor is None else [r for r in stars if r["average_reward"] >= reward_floor]
    if not candidates:
        candidates = stars

    grouped: dict[float, list[dict]] = {}
    for row in candidates:
        grouped.setdefault(float(row["gamma"]), []).append(row)
    best_gamma = max(
        grouped,
        key=lambda g: (
            mean(x["buchi_frequency"] for x in grouped[g]),
            mean(x["average_reward"] for x in grouped[g]),
        ),
    )
    return grouped[best_gamma]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("checkpoints/factorybot_results.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores.json"))
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    best_stars = best_stars_by_reward(rows)
    filtered = [r for r in rows if r["method"] in {"unshielded", "apply_naive"}] + best_stars
    agg = aggregate(filtered)
    scores = {
        "experiments": {
            "factorybot_buchi_reward_tradeoff": {
                "results": agg,
            }
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
