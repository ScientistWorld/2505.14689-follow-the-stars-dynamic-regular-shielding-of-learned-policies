"""Assemble the audit guide directories under tmp/hardening_specs/.

* ``test/``     -- reference + every audit variant and shortcut spec
* ``train/``    -- reference + variants whose train/test behaviour matters
* ``ref_only/`` -- reference alone (seed-noise study)

The seed-replay shortcut spec is built here from the method's visible-suite
gamma sweep: for every visible grid and budget it stores the gamma with the
best observed outcome on that grid and seed, keyed by a grid fingerprint;
unknown grids fall back to the reference table.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from redteam.hardening.guides.shortcuts import fingerprint  # noqa: E402

BUDGETS = (0.1, 0.2, 0.3, 0.4)
HERE = ROOT / "redteam/hardening"
DEST = ROOT / "tmp/hardening_specs"


def seed_replay_spec(reference: dict) -> dict:
    suite = {g["name"]: g for g in json.loads((ROOT / "data/factorybot_suite.json").read_text())}
    rows: dict[str, dict] = {}
    for line in (ROOT / "checkpoints/stars_sweep.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            rows.setdefault(r["instance"], {})[r["gamma"]] = r
    per_instance = {}
    for name, by_gamma in rows.items():
        nominal = by_gamma[None]["average_reward"]
        gammas = sorted(g for g in by_gamma if g is not None)
        table = {}
        for b in BUDGETS:
            def value(g):
                r = by_gamma[g]
                return r["buchi_frequency"] if nominal - r["average_reward"] <= b + 1e-12 else 0.0
            table[f"{b:g}"] = max(gammas, key=lambda g: (value(g), -g))
        g = suite[name]
        per_instance[fingerprint(g["size"], g["walls"], [g["buchi"]])] = table
    return {
        "name": "seed_replay",
        "module": "redteam/hardening/guides/shortcuts.py",
        "factory": "make_seed_replay_guide",
        "params": {
            "theta": reference["params"]["theta"],
            "fallback_gamma_by_budget": reference["params"]["gamma_by_budget"],
            "per_instance": per_instance,
        },
        "audit_role": "old 'seed replay' shortcut: per-grid gamma picked from visible-suite outcomes",
    }


def main() -> None:
    reference = json.loads((ROOT / "checkpoints/guides/apply_stars.json").read_text())
    replay = seed_replay_spec(reference)
    if DEST.exists():
        shutil.rmtree(DEST)
    for sub, source in (("test", HERE / "specs_test"), ("train", HERE / "specs_train"), ("ref_only", None)):
        d = DEST / sub
        d.mkdir(parents=True)
        (d / "apply_stars.json").write_text(json.dumps(reference, indent=2) + "\n")
        if source is not None:
            for spec in sorted(source.glob("*.json")):
                shutil.copy(spec, d / spec.name)
            (d / "seed_replay.json").write_text(json.dumps(replay) + "\n")
    print(f"[build_specs] wrote {DEST} ({len(replay['params']['per_instance'])} replay grids)")


if __name__ == "__main__":
    main()
