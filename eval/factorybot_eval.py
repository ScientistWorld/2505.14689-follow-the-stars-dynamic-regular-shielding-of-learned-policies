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


SCORED_METRICS = (
    "buchi_frequency",
    "reward_gap_to_nominal",
    "buchi_frequency_gain_over_naive",
)

DIAGNOSTIC_METRICS = (
    "average_reward",
    "mean_tv_interference",
    "override_rate",
)


def nominal_rewards(rows: list[dict]) -> dict[str, float]:
    return {
        row["instance"]: row["average_reward"]
        for row in rows
        if row["method"] == "unshielded"
    }


def with_reward_gap(rows: list[dict], nominal: dict[str, float]) -> list[dict]:
    out = []
    for row in rows:
        copied = dict(row)
        copied["reward_gap_to_nominal"] = max(
            0.0,
            nominal.get(row["instance"], row["average_reward"]) - row["average_reward"],
        )
        out.append(copied)
    return out


def aggregate(rows: list[dict], *, scored_only: bool = True) -> dict[str, dict[str, float]]:
    by_method: dict[str, list[dict]] = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)

    naive_freq = mean(x["buchi_frequency"] for x in by_method.get("apply_naive", [])) if "apply_naive" in by_method else 0.0
    out = {}
    for method, items in by_method.items():
        metrics = {
            "buchi_frequency": mean(x["buchi_frequency"] for x in items),
            "reward_gap_to_nominal": mean(x["reward_gap_to_nominal"] for x in items),
            "buchi_frequency_gain_over_naive": mean(x["buchi_frequency"] for x in items) - naive_freq,
        }
        if not scored_only:
            metrics.update(
                {
                    "average_reward": mean(x["average_reward"] for x in items),
                    "mean_tv_interference": mean(x["mean_tv_interference"] for x in items),
                    "override_rate": mean(x["override_rate"] for x in items),
                }
            )
        out[method] = metrics
    return out


def best_stars_by_reward_gap(rows: list[dict], reward_gap_budget: float) -> tuple[float | None, list[dict]]:
    stars = [r for r in rows if r["method"] == "apply_stars"]
    if not stars:
        return None, []

    grouped: dict[float, list[dict]] = {}
    for row in stars:
        grouped.setdefault(float(row["gamma"]), []).append(row)
    candidates = {
        gamma: items
        for gamma, items in grouped.items()
        if mean(x["reward_gap_to_nominal"] for x in items) <= reward_gap_budget
    }
    if not candidates:
        candidates = grouped

    best_gamma = max(
        candidates,
        key=lambda g: (
            mean(x["buchi_frequency"] for x in candidates[g]),
            -mean(x["reward_gap_to_nominal"] for x in candidates[g]),
        ),
    )
    return best_gamma, grouped[best_gamma]


def category_diagnostics(rows: list[dict]) -> dict[str, dict]:
    out = {}
    categories = sorted({row["category"] for row in rows})
    for category in categories:
        subset = [row for row in rows if row["category"] == category]
        out[category] = {"results": aggregate(subset, scored_only=False)}
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("checkpoints/factorybot_results.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores.json"))
    parser.add_argument("--reward-gap-budget", type=float, default=0.4)
    args = parser.parse_args()

    raw_rows = read_jsonl(args.input)
    rows = with_reward_gap(raw_rows, nominal_rewards(raw_rows))
    selected_gamma, best_stars = best_stars_by_reward_gap(rows, args.reward_gap_budget)
    filtered = [r for r in rows if r["method"] in {"unshielded", "apply_naive"}] + best_stars
    agg = aggregate(filtered, scored_only=True)
    scores = {
        "experiments": {
            "factorybot_buchi_reward_tradeoff": {
                "results": agg,
            },
            "_diagnostics": {
                "reward_gap_budget": args.reward_gap_budget,
                "selected_gamma": selected_gamma if selected_gamma is not None else -1.0,
                "metrics": list(SCORED_METRICS + DIAGNOSTIC_METRICS),
                "by_category": category_diagnostics(filtered),
            },
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
