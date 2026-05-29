"""Held-out test-slice evaluation for FactoryBot shielding outputs.

This evaluator reads the same method-agnostic JSONL artifact as the train
slice. When train scores are present, it scores exactly the method entries and
train-selected configurations from that file on held-out instances.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean


EXPERIMENT = "factorybot_buchi_reward_tradeoff"
SPLIT_SEED = "factorybot-visible-train-v1"
SLICE = "test"
BASELINE_METHODS = {"unshielded", "apply_naive"}

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


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def stable_rank(seed: str, category: str, instance: str) -> tuple[int, str]:
    digest = hashlib.sha256(f"{seed}:{category}:{instance}".encode("utf-8")).hexdigest()
    return int(digest, 16), instance


def split_instance_sets(rows: list[dict]) -> dict[str, set[str]]:
    by_category: dict[str, set[str]] = {}
    for row in rows:
        by_category.setdefault(row["category"], set()).add(row["instance"])

    train_instances: set[str] = set()
    test_instances: set[str] = set()
    for category_index, category in enumerate(sorted(by_category)):
        ordered = sorted(
            by_category[category],
            key=lambda instance: stable_rank(SPLIT_SEED, category, instance),
        )
        extra_to_train = category_index % 2 == 0
        train_count = len(ordered) // 2 + (1 if len(ordered) % 2 and extra_to_train else 0)
        train_instances.update(ordered[:train_count])
        test_instances.update(ordered[train_count:])

    return {"train": train_instances, "test": test_instances}


def slice_rows(rows: list[dict]) -> tuple[list[dict], dict[str, set[str]]]:
    split = split_instance_sets(rows)
    return [row for row in rows if row["instance"] in split[SLICE]], split


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

    naive_freq = (
        mean(x["buchi_frequency"] for x in by_method["apply_naive"])
        if "apply_naive" in by_method
        else 0.0
    )
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


def config_tuple(config: dict) -> tuple:
    return (
        config.get("gamma"),
        config.get("theta"),
        config.get("config"),
    )


def serialize_config(key: tuple) -> dict:
    return {
        "gamma": key[0],
        "theta": key[1],
        "config": key[2],
    }


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
        selection[method] = serialize_config(best_key)

    return selected, selection


def load_train_selection(path: Path) -> tuple[list[str], dict[str, dict]] | None:
    if not path.exists():
        return None

    scores = json.loads(path.read_text())
    experiment = scores.get("experiments", {}).get(EXPERIMENT, {})
    results = experiment.get("results", {})
    method_names = sorted(results)
    selected_configs = scores.get("experiments", {}).get("_diagnostics", {}).get("selected_configs", {})
    return method_names, selected_configs


def select_rows_from_train_scores(
    rows: list[dict],
    method_names: list[str],
    selected_configs: dict[str, dict],
) -> tuple[list[dict], dict[str, dict]]:
    available_methods = {row["method"] for row in rows}
    missing_methods = sorted(set(method_names) - available_methods)
    if missing_methods:
        raise ValueError(f"Test artifact is missing train-scored methods: {missing_methods}")

    selected: list[dict] = []
    applied_configs: dict[str, dict] = {}
    for method in method_names:
        method_rows = [row for row in rows if row["method"] == method]
        if method in BASELINE_METHODS or method not in selected_configs:
            selected.extend(method_rows)
            continue

        expected_key = config_tuple(selected_configs[method])
        matched = [row for row in method_rows if method_config_key(row) == expected_key]
        if not matched:
            raise ValueError(
                f"Test artifact has method {method!r} but not its train-selected config "
                f"{selected_configs[method]!r}"
            )
        selected.extend(matched)
        applied_configs[method] = selected_configs[method]

    return selected, applied_configs


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


def split_diagnostics(split: dict[str, set[str]]) -> dict:
    return {
        name: {
            "instance_count": len(instances),
            "instances": sorted(instances),
        }
        for name, instances in split.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("checkpoints/factorybot_results.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("scoring/scores_test.json"))
    parser.add_argument("--train-scores", type=Path, default=Path("scoring/scores_train.json"))
    parser.add_argument("--reward-gap-budget", type=float, default=0.4)
    args = parser.parse_args()

    raw_rows = read_jsonl(args.input)
    sliced_raw_rows, split = slice_rows(raw_rows)
    rows = with_reward_gap(sliced_raw_rows, nominal_rewards(sliced_raw_rows))

    train_selection = load_train_selection(args.train_scores)
    if train_selection is None:
        filtered, selected_configs = select_rows_by_reward_gap(
            rows,
            args.reward_gap_budget,
            baseline_methods=BASELINE_METHODS,
        )
        selection_source = "held_out_slice_fallback_no_train_scores"
        train_method_names = sorted({row["method"] for row in filtered})
    else:
        train_method_names, train_selected_configs = train_selection
        filtered, selected_configs = select_rows_from_train_scores(
            rows,
            train_method_names,
            train_selected_configs,
        )
        selection_source = str(args.train_scores)

    agg = aggregate(filtered, scored_only=True)
    expected_methods = sorted(train_method_names)
    actual_methods = sorted(agg)
    if actual_methods != expected_methods:
        raise ValueError(
            f"Test results keys {actual_methods} do not match train-scored methods {expected_methods}"
        )

    scores = {
        "experiments": {
            EXPERIMENT: {
                "results": agg,
            },
            "_diagnostics": {
                "slice": SLICE,
                "split_seed": SPLIT_SEED,
                "split": split_diagnostics(split),
                "reward_gap_budget": args.reward_gap_budget,
                "selected_configs": selected_configs,
                "selection_source": selection_source,
                "train_scored_methods": train_method_names,
                "evaluated_artifact": str(args.input),
                "run": run_diagnostics(filtered),
                "raw_slice_artifact": run_diagnostics(rows),
                "metrics": list(SCORED_METRICS + DIAGNOSTIC_METRICS),
                "by_category": category_diagnostics(filtered),
            },
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
