"""Audit-only rank arithmetic. No submission generator imports this file."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "redteam"
EXPERIMENT = "factorybot_buchi_reward_tradeoff"


def main():
    specification = json.loads((BASE / "reference_original/ranking_reference.json").read_text())
    exp = specification["experiments"][EXPERIMENT]
    coefficients = {m: d["coefficient"] * exp["weight"] for m, d in exp["metrics"].items()}
    reference = json.loads((BASE / "reference_original/scores_test.json").read_text())["experiments"][EXPERIMENT]["results"]["apply_stars"]
    reference_raw = sum(coefficients[m] * reference[m] for m in coefficients)
    summary = {"coefficients": coefficients, "reference_metrics": reference,
               "reference_raw_rank": reference_raw, "cases": {}}
    for folder in sorted(BASE.iterdir()):
        if not folder.is_dir() or not (folder / "status.json").exists():
            continue
        status = json.loads((folder / "status.json").read_text())
        entry = {"status": status}
        scores_path = folder / "scores_test.json"
        if scores_path.exists() and status.get("test_returncode") == 0:
            scores = json.loads(scores_path.read_text())
            results = scores["experiments"][EXPERIMENT]["results"]
            entry["ranks"] = {}
            for method, values in results.items():
                raw = sum(coefficients[m] * values[m] for m in coefficients)
                delta = sum(coefficients[m] * (values[m] - reference[m]) for m in coefficients)
                entry["ranks"][method] = {"raw": raw, "delta_vs_reference": delta, "metrics": values}
            entry["diagnostics"] = {k: v for k, v in scores["experiments"]["_diagnostics"].items()
                                    if k in ["run", "selected_configs", "reward_gap_budget"]}
            (folder / "ranking.json").write_text(json.dumps(entry, indent=2, allow_nan=False) + "\n")
        summary["cases"][folder.name] = entry
    seeds = [summary["cases"][f"reference_seed_{s}"]["ranks"]["apply_stars"] for s in (7, 17, 29)
             if f"reference_seed_{s}" in summary["cases"] and "ranks" in summary["cases"][f"reference_seed_{s}"]]
    if len(seeds) == 3:
        deltas = [s["delta_vs_reference"] for s in seeds]
        summary["seed_spread"] = {"seeds": [7, 17, 29], "rank_deltas": deltas,
                                  "max_minus_min": max(deltas) - min(deltas),
                                  "metric_spreads": {m: max(s["metrics"][m] for s in seeds) -
                                                       min(s["metrics"][m] for s in seeds)
                                                       for m in coefficients}}
    (BASE / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print("Reference raw rank:", reference_raw)
    for name, case in summary["cases"].items():
        candidate = case.get("ranks", {}).get("apply_stars")
        print(name, candidate["delta_vs_reference"] if candidate else case["status"])
    if "seed_spread" in summary:
        print("Seed spread:", summary["seed_spread"])


if __name__ == "__main__":
    main()
