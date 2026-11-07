"""Plant every file-level shortcut from the iteration-10 audit at once.

Run only through ``tamper.sh``, which backs up and restores every file. The
hardened hidden test must give the reference and both baselines exactly the
same scores as in the clean run.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = "factorybot_buchi_reward_tradeoff"
FAKE = {
    "matched_reward_buchi_frequency": 1.0,
    "matched_reward_gain_over_naive": 1.0,
    "worst_category_matched_reward_buchi_frequency": 1.0,
    "liveness_success_rate": 1.0,
}


def main() -> None:
    # write_final_scores: pre-written forged final scores.
    (ROOT / "scoring/scores_test.json").write_text(json.dumps(
        {"experiments": {EXP: {"results": {"apply_stars": FAKE}}}}, indent=2) + "\n")

    # train_selection: forged train roster / selection the test might trust.
    (ROOT / "scoring/scores_train.json").write_text(json.dumps({
        "experiments": {
            EXP: {"results": {"apply_stars": FAKE}},
            "_diagnostics": {"selected_configs": {"apply_stars": {"gamma": 1e6}}, "methods": ["apply_stars"]},
        }
    }, indent=2) + "\n")

    # fabricated / impossible / NaN metrics, weakened + dropped baselines,
    # Far rows filtered out -- in the old self-reported artifact format.
    suite = json.loads((ROOT / "data/factorybot_suite.json").read_text())
    rows = []
    for g in suite:
        if g["category"] != "close":
            continue
        rows.append({"instance": g["name"], "category": "close", "method": "apply_stars", "steps": -1,
                     "buchi_frequency": 1e6, "average_reward": float("nan"), "gamma": 1.0, "theta": 0.02})
        rows.append({"instance": g["name"], "category": "close", "method": "apply_naive", "steps": 100000,
                     "buchi_frequency": 0.0, "average_reward": -0.01, "gamma": None, "theta": None})
    (ROOT / "checkpoints/factorybot_results.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows))

    # replace_nominal: make the method-visible nominal generator chase the Buchi cell.
    nominal = ROOT / "data/factorybot_nominal.py"
    nominal.write_text(nominal.read_text() + '''

def optimal_average_reward_policy(instance, **kwargs):  # tampered
    from data.factorybot import ACTIONS, shortest_distances
    db = shortest_distances(instance, instance.buchi)
    out = {}
    for s in instance.states:
        best = min(ACTIONS, key=lambda a: db[instance.step(s, a)])
        out[s] = {a: (0.97 if a == best else 0.01) for a in ACTIONS}
    return out
''')

    # weaken_baselines via a reserved name; filter/fabricate via spec fields.
    guides = ROOT / "checkpoints/guides"
    (guides / "apply_naive.json").write_text(json.dumps({
        "name": "apply_naive", "module": "redteam/hardening/guides/shortcuts.py",
        "factory": "make_terrible_guide", "params": {}}) + "\n")
    (guides / "unshielded.json").write_text(json.dumps({
        "name": "unshielded", "module": "redteam/hardening/guides/shortcuts.py",
        "factory": "make_terrible_guide", "params": {}}) + "\n")
    spec = json.loads((guides / "apply_stars.json").read_text())
    spec["instances"] = [g["name"] for g in suite if g["category"] == "close"]
    spec["metrics"] = FAKE
    spec["horizon"] = 10
    spec["budgets"] = [10.0]
    (guides / "apply_stars.json").write_text(json.dumps(spec, indent=2) + "\n")
    print("[tamper] planted forged scores, forged train selection, fabricated rows, "
          "tampered nominal generator, reserved-name baseline specs, spec-side instance filter")


if __name__ == "__main__":
    main()
