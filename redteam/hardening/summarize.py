"""Summarize the hardening audit: rank deltas, tamper check, seed noise, paired SEs."""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "redteam/hardening/out"
ROWS = ROOT / "tmp/hardening_rows"
EXP = "factorybot_buchi_reward_tradeoff"
REF = "apply_stars"
BASELINES = ("unshielded", "apply_naive")


def coefficients() -> dict:
    ref = json.loads((ROOT / "scoring/reference.json").read_text())
    return {k: v["coefficient"] for k, v in ref["experiments"][EXP]["metrics"].items()}


def load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())["experiments"]


def raw(metrics: dict, coef: dict) -> float:
    return sum(c * metrics[k] for k, c in coef.items())


def table(exps, coef, reference_metrics=None) -> dict:
    results = exps[EXP]["results"]
    ref = reference_metrics or results[REF]
    out = {}
    for name, metrics in sorted(results.items()):
        status = exps["_diagnostics"]["methods"].get(name, {}).get("status", "ok")
        out[name] = {
            "status": status,
            "reason": exps["_diagnostics"]["methods"].get(name, {}).get("reason"),
            "raw": raw(metrics, coef),
            "delta_vs_reference": raw(metrics, coef) - raw(ref, coef),
            "metrics": metrics,
        }
    return out


def paired(rows_path: Path, methods: list[str]) -> dict:
    if not rows_path.exists():
        return {}
    per = {}
    for line in rows_path.read_text().splitlines():
        r = json.loads(line)
        within = r["nominal_reward"] - r["average_reward"] <= r["budget"] + 1e-12
        gated = r["buchi_frequency"] if within else 0.0
        live = 1.0 if within and r["buchi_frequency"] >= 1.0 / r["n_states"] else 0.0
        # per-instance contribution to the separable part of the rank:
        # (1.0 + 0.5) * matched frequency + 0.25 * liveness, averaged over budgets
        per.setdefault(r["method"], {}).setdefault(r["instance"], []).append(1.5 * gated + 0.25 * live)
    if REF not in per:
        return {}
    base = {k: sum(v) / len(v) for k, v in per[REF].items()}
    out = {}
    for m in methods:
        if m not in per:
            continue
        diffs = [sum(v) / len(v) - base[k] for k, v in per[m].items()]
        n = len(diffs)
        mean = sum(diffs) / n
        sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / (n - 1)) if n > 1 else 0.0
        out[m] = {"n": n, "mean_diff": mean, "paired_se": sd / math.sqrt(n), "z": mean / (sd / math.sqrt(n)) if sd else None}
    return out


def main() -> None:
    coef = coefficients()
    summary = {"coefficients": coef}
    clean = load(ROOT / "scoring/scores_test.json")
    clean_ref = clean[EXP]["results"][REF]
    summary["reference_test_raw"] = raw(clean_ref, coef)
    summary["reference_test_metrics"] = clean_ref
    summary["baselines_test"] = {b: clean[EXP]["results"][b] for b in BASELINES}

    variants = load(OUT / "test_variants.json")
    if variants:
        summary["test_variants"] = table(variants, coef, clean_ref)
        summary["test_variants_consistent_reference"] = variants[EXP]["results"][REF] == clean_ref
        summary["test_rejected_specs"] = variants["_diagnostics"]["rejected_specs"]
        summary["test_paired"] = paired(ROWS / "test_variants.jsonl",
                                        [m for m in variants[EXP]["results"] if m != REF])

    tamper = load(OUT / "tamper_scores_test.json")
    if tamper:
        same = {m: tamper[EXP]["results"].get(m) == clean[EXP]["results"][m] for m in (REF,) + BASELINES}
        summary["tamper"] = {
            "identical_to_clean": same,
            "methods_scored": sorted(tamper[EXP]["results"]),
            "rejected_specs": tamper["_diagnostics"]["rejected_specs"],
            "delta_vs_clean_reference": raw(tamper[EXP]["results"][REF], coef) - raw(clean_ref, coef),
        }

    noise = {"default": raw(clean_ref, coef)}
    effect = {"default": clean_ref["matched_reward_gain_over_naive"]}
    for salt in ("alt1", "alt2"):
        exps = load(OUT / f"test_noise_{salt}.json")
        if exps:
            noise[salt] = raw(exps[EXP]["results"][REF], coef)
            effect[salt] = exps[EXP]["results"][REF]["matched_reward_gain_over_naive"]
    summary["seed_noise"] = {
        "reference_raw_by_rng_salt": noise,
        "max_minus_min": max(noise.values()) - min(noise.values()),
        "stars_minus_naive_matched_frequency_by_salt": effect,
    }

    train = load(OUT / "train_variants.json")
    if train:
        summary["train_variants"] = table(train, coef)
        summary["train_paired"] = paired(ROWS / "train_variants.jsonl",
                                         [m for m in train[EXP]["results"] if m != REF])
    clean_train = load(ROOT / "scoring/scores_train.json")
    if clean_train:
        summary["reference_train_raw"] = raw(clean_train[EXP]["results"][REF], coef)
        summary["reference_train_metrics"] = clean_train[EXP]["results"][REF]

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"reference test raw {summary['reference_test_raw']:.6f}")
    for key in ("test_variants", "train_variants"):
        if key in summary:
            print(f"== {key}")
            for name, row in summary[key].items():
                m = row["metrics"]
                print(f"  {name:22s} {row['status']:6s} delta={row['delta_vs_reference']:+.5f} "
                      f"F={m['matched_reward_buchi_frequency']:.4f} worst={m['worst_category_matched_reward_buchi_frequency']:.4f} "
                      f"LS={m['liveness_success_rate']:.3f}")
    print("seed noise", json.dumps(summary["seed_noise"]))
    if "tamper" in summary:
        print("tamper", json.dumps(summary["tamper"]))


if __name__ == "__main__":
    main()
