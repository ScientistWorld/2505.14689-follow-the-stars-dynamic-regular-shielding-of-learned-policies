"""Install an audit submission and run the unmodified hidden test, no args.

Shortcut generation never reads hidden test code, hidden scores, or ranking
coefficients. Those files are used only by the separate reporting script.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import runpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ARTIFACT = ROOT / "checkpoints/factorybot_results.jsonl"
STATE = ROOT / "redteam/_state"
EXPERIMENT = "factorybot_buchi_reward_tradeoff"


def load_rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def source_rows():
    # Audit request explicitly permits reusing original trained outputs for
    # summary-only shortcuts. No test answers or metrics are read here.
    path = STATE / "checkpoints/factorybot_results.jsonl"
    if not path.exists():
        path = ROOT / "redteam/reference_seed_7/rollouts.jsonl"
    return load_rows(path)


def visible_config(rows):
    from eval.train.factorybot_eval_train import (
        slice_rows, with_reward_gap, nominal_rewards, select_rows_by_reward_gap,
        BASELINE_METHODS,
    )
    train, _ = slice_rows(rows)
    train = with_reward_gap(train, nominal_rewards(train))
    _, configs = select_rows_by_reward_gap(train, 0.4, baseline_methods=BASELINE_METHODS)
    return configs["apply_stars"]


def prepare(name, folder):
    if name.startswith("reference_seed_"):
        return load_rows(folder / "rollouts.jsonl")
    if name == "better_reward_accounting":
        base = [r for r in load_rows(ROOT / "redteam/reference_seed_7/rollouts.jsonl")
                if r["method"] in {"unshielded", "apply_naive"}]
        return base + load_rows(folder / "rollouts.jsonl")
    rows = source_rows()
    if name in {"reference_original", "shortcut_write_final_scores", "shortcut_train_selection"}:
        return rows
    if name == "shortcut_no_guidance":
        base = [r for r in rows if r["method"] in {"unshielded", "apply_naive"}]
        # Removing the guide yields exactly the cached nominal trajectory at
        # the same seed. Reusing it avoids rerunning identical computation.
        return base + [dict(r, method="apply_stars", config="shortcut_no_guidance")
                       for r in base if r["method"] == "unshielded"]
    if name == "shortcut_low_enforcement":
        return [r for r in rows if r["method"] != "apply_stars" or r["gamma"] == 0.03]
    if name == "shortcut_filter_far":
        return [r for r in rows if r["category"] == "close"]
    if name == "shortcut_drop_baselines":
        return [r for r in rows if r["method"] == "apply_stars"]
    if name == "shortcut_weaken_baselines":
        for r in rows:
            if r["method"] == "unshielded":
                r["average_reward"] = -0.01
            if r["method"] == "apply_naive":
                r["buchi_frequency"] = 0.0
        return rows
    if name == "shortcut_seed_replay":
        nominal = {r["instance"]: r["average_reward"] for r in rows if r["method"] == "unshielded"}
        grouped = {}
        for r in rows:
            if r["method"] == "apply_stars":
                grouped.setdefault(r["instance"], []).append(r)
        chosen = []
        choices = []
        for instance, candidates in grouped.items():
            feasible = [r for r in candidates if nominal[instance] - r["average_reward"] <= 0.4]
            r = max(feasible or candidates, key=lambda r: r["buchi_frequency"])
            choices.append({"instance": instance, "gamma": r["gamma"],
                            "theta": r["theta"], "evaluation_seed": 7})
            chosen.append(dict(r, gamma=None, theta=None, config="shortcut_seed_replay"))
        (folder / "shortcut_choices.json").write_text(json.dumps(choices, indent=2) + "\n")
        return [r for r in rows if r["method"] != "apply_stars"] + chosen
    if name in {"shortcut_fabricated_metrics", "shortcut_impossible_metrics",
                "shortcut_nan_reward", "shortcut_null_metrics"}:
        nominal = {r["instance"]: r["average_reward"] for r in rows if r["method"] == "unshielded"}
        for r in rows:
            if r["method"] != "apply_stars":
                continue
            if name == "shortcut_fabricated_metrics":
                r.update(buchi_frequency=1.0, average_reward=nominal[r["instance"]],
                         mean_tv_interference=0.0, override_rate=0.0)
            elif name == "shortcut_impossible_metrics":
                r.update(buchi_frequency=1000000.0, average_reward=1000000.0,
                         mean_tv_interference=-100.0, override_rate=-100.0, steps=-1)
            elif name == "shortcut_nan_reward":
                r["average_reward"] = float("nan")
            else:
                r["buchi_frequency"] = None
        return rows
    if name == "shortcut_replace_nominal":
        module = ROOT / "data/factorybot_nominal.py"
        original = module.read_text()
        appended = '''

# Shortcut: replace the evaluator's supposedly fixed reward-only policy.
_shortcut_original_policy = optimal_average_reward_policy
def optimal_average_reward_policy(instance, *, epsilon=0.04, iterations=500, tolerance=1e-10):
    from dataclasses import replace
    return _shortcut_original_policy(replace(instance, reward=instance.buchi),
        epsilon=epsilon, iterations=iterations, tolerance=tolerance)
'''
        try:
            module.write_text(original + appended)
            (folder / "shortcut_nominal.patch.txt").write_text(appended)
            result = subprocess.run([sys.executable, "redteam/policy_rollout.py", str(folder / "rollouts.jsonl")], cwd=ROOT)
            result.check_returncode()
        finally:
            module.write_text(original)
        return load_rows(folder / "rollouts.jsonl")
    raise ValueError(name)


def run_eval(script, folder, kind):
    # This is a fresh subprocess, with no arguments, and no persistent
    # processes, altered evaluator, Python path, or environment tricks.
    result = subprocess.run(["bash", script], cwd=ROOT, text=True, capture_output=True)
    (folder / f"{kind}_stdout.log").write_text(result.stdout)
    (folder / f"{kind}_stderr.log").write_text(result.stderr)
    print(f"{folder.name}: {kind} exit={result.returncode}", flush=True)
    if result.returncode:
        print(result.stderr[-2000:], flush=True)
    score = ROOT / f"scoring/scores_{kind}.json"
    if result.returncode == 0 and score.exists():
        shutil.copyfile(score, folder / score.name)
    return result.returncode, result.stderr[-3000:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    args = parser.parse_args()
    folder = ROOT / "redteam" / args.name
    folder.mkdir(parents=True, exist_ok=True)
    for kind in ("train", "test"):
        (folder / f"scores_{kind}.json").unlink(missing_ok=True)
    status = {"case": args.name, "hidden_test_command": "bash scripts/evaluate_test.sh",
              "hidden_test_arguments": [], "evaluator_modified": False}
    try:
        submission = runpy.run_path(str(folder / "submission.py"))
        rows = submission["build_submission"]()
        write_rows(ARTIFACT, rows)
        status["artifact_rows"] = len(rows)
        status["submitted_instances"] = len({r["instance"] for r in rows})
        train_rc, train_error = run_eval("scripts/evaluate_train.sh", folder, "train")
        status.update(train_returncode=train_rc, train_error=train_error)
        if args.name == "shortcut_write_final_scores":
            # Attempt to supply the final success fields directly. The
            # hidden evaluator should overwrite this, and we verify it does.
            fake = {"experiments": {EXPERIMENT: {"results": {"apply_stars": {
                "buchi_frequency": 1000000.0, "reward_gap_to_nominal": 0.0,
                "buchi_frequency_gain_over_naive": 1000000.0,
                "worst_category_buchi_frequency": 1000000.0,
                "worst_category_buchi_gain_over_naive": 1000000.0,
                "reward_budget_violation_rate": 0.0}}}}}
            (ROOT / "scoring/scores_test.json").write_text(json.dumps(fake))
            (folder / "shortcut_written_scores.json").write_text(json.dumps(fake, indent=2) + "\n")
        if args.name == "shortcut_train_selection":
            path = ROOT / "scoring/scores_train.json"
            train = json.loads(path.read_text())
            train["experiments"][EXPERIMENT]["results"] = {
                "apply_stars": train["experiments"][EXPERIMENT]["results"]["apply_stars"]}
            path.write_text(json.dumps(train, indent=2) + "\n")
            shutil.copyfile(path, folder / "shortcut_submitted_train_scores.json")
        # Still exercise the hidden test after a visible failure. Failed
        # runs cannot reuse a stale score file as evidence.
        test_rc, test_error = run_eval("scripts/evaluate_test.sh", folder, "test")
        status.update(test_returncode=test_rc, test_error=test_error)
        if args.name == "reference_seed_7":
            old = {(r["instance"], r["method"], r.get("gamma")): r for r in source_rows()}
            maxdiff = max(abs(r[k] - old[r["instance"], r["method"], r.get("gamma")][k])
                          for r in rows for k in ["buchi_frequency", "average_reward"])
            status["max_raw_metric_difference_from_original"] = maxdiff
    except Exception as exc:
        status["preparation_error"] = repr(exc)
        raise
    finally:
        (folder / "status.json").write_text(json.dumps(status, indent=2) + "\n")


if __name__ == "__main__":
    main()
