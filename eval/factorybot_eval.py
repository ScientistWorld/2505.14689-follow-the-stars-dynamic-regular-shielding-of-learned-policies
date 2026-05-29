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


def method_config_key(row: dict) -> tuple:
    return (
        row.get("gamma"),
        row.get("theta"),
        row.get("config"),
    )


def select_rows_by_reward_gap(
    rows: list[dict],
    reward_gap_budget: float,
    *,
    baseline_methods: set[str],
) -> tuple[list[dict], dict[str, dict]]:
    selected = [row for row in rows if row["method"] in baseline_methods]
    selection: dict[str, dict] = {}

    candidate_methods = sorted({row["method"] for row in rows} - baseline_methods)
    for method in candidate_methods:
        method_rows = [row for row in rows if row["method"] == method]
        grouped: dict[tuple, list[dict]] = {}
        for row in method_rows:
            grouped.setdefault(method_config_key(row), []).append(row)

        candidates = {
            key: items
            for key, items in grouped.items()
            if mean(x["reward_gap_to_nominal"] for x in items) <= reward_gap_budget
        }
        if not candidates:
            candidates = grouped

        best_key = max(
            candidates,
            key=lambda key: (
                mean(x["buchi_frequency"] for x in candidates[key]),
                -mean(x["reward_gap_to_nominal"] for x in candidates[key]),
            ),
        )
        selected.extend(grouped[best_key])
        selection[method] = {
            "gamma": best_key[0],
            "theta": best_key[1],
            "config": best_key[2],
        }

    return selected, selection


def category_diagnostics(rows: list[dict]) -> dict[str, dict]:
    out = {}
    categories = sorted({row["category"] for row in rows})
    for category in categories:
        subset = [row for row in rows if row["category"] == category]
        out[category] = {"results": aggregate(subset, scored_only=False)}
    return out


def run_diagnostics(rows: list[dict]) -> dict:
    instances = sorted({row["instance"] for row in rows})
    categories = sorted({row["category"] for row in rows})
    methods = sorted({row["method"] for row in rows})
    steps = sorted({int(row["steps"]) for row in rows})
    gammas = sorted({float(row["gamma"]) for row in rows if row.get("gamma") is not None})
    return {
        "row_count": len(rows),
        "instance_count": len(instances),
        "categories": {
            category: len({row["instance"] for row in rows if row["category"] == category})
            for category in categories
        },
        "methods": methods,
        "steps": steps,
        "stars_gammas": gammas,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("checkpoints/factorybot_results.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores.json"))
    parser.add_argument("--reward-gap-budget", type=float, default=0.4)
    args = parser.parse_args()

    raw_rows = read_jsonl(args.input)
    rows = with_reward_gap(raw_rows, nominal_rewards(raw_rows))
    filtered, selected_configs = select_rows_by_reward_gap(
        rows,
        args.reward_gap_budget,
        baseline_methods={"unshielded", "apply_naive"},
    )
    agg = aggregate(filtered, scored_only=True)
    scores = {
        "experiments": {
            "factorybot_buchi_reward_tradeoff": {
                "results": agg,
            },
            "_diagnostics": {
                "reward_gap_budget": args.reward_gap_budget,
                "selected_gamma": (
                    selected_configs.get("apply_stars", {}).get("gamma")
                    if "apply_stars" in selected_configs
                    else -1.0
                ),
                "selected_configs": selected_configs,
                "evaluated_artifact": str(args.input),
                "run": run_diagnostics(filtered),
                "raw_artifact": run_diagnostics(rows),
                "metrics": list(SCORED_METRICS + DIAGNOSTIC_METRICS),
                "by_category": category_diagnostics(filtered),
            },
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
