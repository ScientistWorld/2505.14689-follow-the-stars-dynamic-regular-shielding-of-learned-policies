"""Tune and package ApplySTARs for the FactoryBot runtime-guide benchmark.

1. Sweep the enforcement parameter gamma over the paper's grid
   (1e-3 ... 1, Fig. 4a) on every grid of the visible suite at the full
   100,000-step horizon, with theta fixed, alongside the unshielded nominal.
2. For each reward budget, pick the single global gamma that maximizes the
   visible-suite objective (matched-reward Buchi frequency, worst
   Close/Far category, and liveness success; same form as the documented
   ranking) -- no per-instance choices.
3. Write the guide spec ``checkpoints/guides/apply_stars.json`` that the
   scorers load, plus the sweep rows and a gamma-sweep summary (Fig. 4a).
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.factorybot import FactoryBotInstance, read_suite, write_suite  # noqa: E402
from data.factorybot_nominal import optimal_average_reward_policy  # noqa: E402
from data.factorybot_rollout import BUDGETS, HORIZON, GuideModel, rollout_guide, rollout_policy  # noqa: E402
from method.stars_guide import DEFAULT_THETA, StarsGuide  # noqa: E402
from method.template_synthesis import synthesize_buchi_reach_template, template_summary  # noqa: E402

PAPER_GAMMAS = (0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0)


def sweep_instance(task):
    idx, payload, steps, seed_base, gammas, theta = task
    instance = FactoryBotInstance.from_json(payload)
    nominal = optimal_average_reward_policy(instance)
    model = GuideModel(instance, nominal)
    template = synthesize_buchi_reach_template(model, model.buchi)
    seed = seed_base + idx
    base = {
        "instance": instance.name,
        "category": instance.category,
        "n_states": len(instance.states),
        "steps": steps,
        "seed": seed,
    }
    rows = [dict(base, method="unshielded", gamma=None, **rollout_policy(instance, nominal, steps=steps, seed=seed))]
    for gamma in gammas:
        guide = StarsGuide(model, gamma, theta, template=template)
        out = rollout_guide(instance, nominal, guide, steps=steps, seed=seed)
        rows.append(dict(base, method="apply_stars", gamma=gamma, theta=theta, **out, **template_summary(template)))
    return rows


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def budget_objective(rows_by_instance: dict, gamma: float, budget: float) -> dict:
    gated, success, by_cat = [], [], {}
    for inst, rows in rows_by_instance.items():
        nominal = rows[None]["average_reward"]
        r = rows[gamma]
        within = nominal - r["average_reward"] <= budget + 1e-12
        value = r["buchi_frequency"] if within else 0.0
        gated.append(value)
        success.append(1.0 if within and r["buchi_frequency"] >= 1.0 / r["n_states"] else 0.0)
        by_cat.setdefault(r["category"], []).append(value)
    freq = _mean(gated)
    worst = min(_mean(v) for v in by_cat.values())
    live = _mean(success)
    return {
        "matched_reward_buchi_frequency": freq,
        "worst_category": worst,
        "liveness_success_rate": live,
        "objective": 1.5 * freq + 0.5 * worst + 0.25 * live,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=ROOT / "data/factorybot_suite.json")
    parser.add_argument("--steps", type=int, default=HORIZON)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--theta", type=float, default=DEFAULT_THETA)
    parser.add_argument("--gammas", type=float, nargs="+", default=list(PAPER_GAMMAS))
    parser.add_argument("--workers", type=int, default=max(1, min(len(os.sched_getaffinity(0)), 32)))
    parser.add_argument("--sweep-out", type=Path, default=ROOT / "checkpoints/stars_sweep.jsonl")
    parser.add_argument("--spec-out", type=Path, default=ROOT / "checkpoints/guides/apply_stars.json")
    parser.add_argument("--summary-out", type=Path, default=ROOT / "checkpoints/stars_sweep_summary.json")
    parser.add_argument("--regenerate-suite", action="store_true")
    args = parser.parse_args()

    if args.regenerate_suite or not args.suite.exists():
        write_suite(args.suite)
    payloads = json.loads(args.suite.read_text())
    expected = 1 + len(args.gammas)

    # Resume: keep instances whose sweep is complete for this configuration.
    done: dict[str, list[dict]] = {}
    if args.sweep_out.exists():
        for line in args.sweep_out.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("steps") == args.steps:
                    done.setdefault(row["instance"], []).append(row)
        done = {k: v for k, v in done.items() if len(v) == expected
                and sorted(r["gamma"] for r in v if r["gamma"] is not None) == sorted(args.gammas)}
    args.sweep_out.parent.mkdir(parents=True, exist_ok=True)
    args.sweep_out.write_text("".join(json.dumps(r) + "\n" for rows in done.values() for r in rows))

    tasks = [
        (idx, payload, args.steps, args.seed, tuple(args.gammas), args.theta)
        for idx, payload in enumerate(payloads)
        if payload["name"] not in done
    ]
    print(f"[factorybot_method] sweeping {len(tasks)} / {len(payloads)} instances "
          f"({len(args.gammas)} gammas, {args.steps} steps, {args.workers} workers)", flush=True)
    with args.sweep_out.open("a") as handle, ProcessPoolExecutor(max_workers=args.workers) as pool:
        for count, rows in enumerate(pool.map(sweep_instance, tasks, chunksize=1), 1):
            for row in rows:
                handle.write(json.dumps(row) + "\n")
            handle.flush()
            done[rows[0]["instance"]] = rows
            if count % 25 == 0 or count == len(tasks):
                print(f"[factorybot_method] swept {count}/{len(tasks)}", flush=True)

    rows_by_instance = {
        inst: {r["gamma"]: r for r in rows} for inst, rows in done.items()
    }
    selection, table = {}, {}
    for budget in BUDGETS:
        scored = {g: budget_objective(rows_by_instance, g, budget) for g in args.gammas}
        best = max(args.gammas, key=lambda g: (scored[g]["objective"], -g))
        selection[f"{budget:g}"] = best
        table[f"{budget:g}"] = {f"{g:g}": scored[g] for g in args.gammas}

    spec = {
        "name": "apply_stars",
        "module": "method/stars_guide.py",
        "factory": "make_guide",
        "params": {"theta": args.theta, "gamma_by_budget": selection},
        "provenance": f"gamma tuned on the visible {len(rows_by_instance)}-grid suite, {args.steps} steps",
    }
    args.spec_out.parent.mkdir(parents=True, exist_ok=True)
    args.spec_out.write_text(json.dumps(spec, indent=2) + "\n")

    # Fig. 4a-style summary: gamma vs Buchi frequency and reward gap by category.
    sweep = {}
    for gamma in args.gammas:
        for cat in sorted({r[None]["category"] for r in rows_by_instance.values()}):
            sub = [r for r in rows_by_instance.values() if r[None]["category"] == cat]
            sweep.setdefault(f"{gamma:g}", {})[cat] = {
                "buchi_frequency": _mean(r[gamma]["buchi_frequency"] for r in sub),
                "reward_gap_to_nominal": _mean(r[None]["average_reward"] - r[gamma]["average_reward"] for r in sub),
            }
    nominal_summary = {
        cat: _mean(r[None]["buchi_frequency"] for r in rows_by_instance.values() if r[None]["category"] == cat)
        for cat in sorted({r[None]["category"] for r in rows_by_instance.values()})
    }
    args.summary_out.write_text(json.dumps({
        "selected_gamma_by_budget": selection,
        "budget_objective_table": table,
        "gamma_sweep_by_category": sweep,
        "unshielded_buchi_frequency_by_category": nominal_summary,
    }, indent=2, sort_keys=True) + "\n")
    print(f"[factorybot_method] selected gamma by budget: {selection}", flush=True)


if __name__ == "__main__":
    main()
