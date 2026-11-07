"""Hidden-test evaluator for FactoryBot runtime guides.

Everything on the scored side of the comparison is owned by this file:

* the hidden test grids (generated here from seeds that exist only here),
* the simulator, reward function and Buchi region,
* the reward-optimised nominal policy the guide must post-process,
* the rollout random numbers (start states and action sampling),
* the unshielded and naive baselines and their operating points,
* the reward budgets, horizon, and every scored number.

A submitted method is a *runtime guide*: a Python factory named in a JSON
spec under ``checkpoints/guides/*.json``. The evaluator builds one fresh
guide per (instance, budget) run, asks it for an action distribution at
every step, validates that distribution, samples the action itself, and
simulates the transition. Nothing a method writes (rollout rows, metrics,
score files, baseline rows, instance lists) is read or trusted.

The file is intentionally self-contained (standard library only) and shares
no code with ``eval/train/`` or with ``data/`` / ``method/``.
"""

from __future__ import annotations

import argparse
from collections import deque
from collections.abc import Mapping
import hashlib
import importlib.util
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import random
import sys
import traceback
import types


EXPERIMENT = "factorybot_buchi_reward_tradeoff"
SLICE = "test"
WORKSPACE = Path(__file__).resolve().parents[2]

ACTIONS = ("up", "down", "left", "right")
ACTION_INDEX = {a: i for i, a in enumerate(ACTIONS)}
DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))

HORIZON = 100_000
BUDGETS = (0.1, 0.2, 0.3, 0.4)
NOMINAL_EPSILON = 0.04
NAIVE_MIX_GRID = (0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0)
RESERVED_NAMES = ("unshielded", "apply_naive")
PROB_TOL = 1e-6

# Hidden test suite: 128 Close + 128 Far grids, sizes 5..13, same generator
# family as the visible suite but seeds that only exist in this file.
TEST_PER_CATEGORY = 128
_SUITE_SALT = "factorybot-hidden-test-suite-v2"
_ROLLOUT_SALT = "factorybot-hidden-test-rollout-v2"

SCORED_METRICS = (
    "matched_reward_buchi_frequency",
    "matched_reward_gain_over_naive",
    "worst_category_matched_reward_buchi_frequency",
    "liveness_success_rate",
)


# --------------------------------------------------------------------------
# Grid generation and simulation (evaluator-private copy)
# --------------------------------------------------------------------------


def _connected(free: set, size: int, walls: set) -> bool:
    if not free:
        return False
    start = next(iter(free))
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DELTAS:
            nxt = (r + dr, c + dc)
            if 0 <= nxt[0] < size and 0 <= nxt[1] < size and nxt not in walls and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == free


def _generate(seed: int, size: int, category: str, name: str) -> dict:
    rng = random.Random(seed)
    min_frac, max_frac = (0.7, 0.9) if category == "far" else (0.1, 0.2)
    cells = [(r, c) for r in range(size) for c in range(size)]
    for _ in range(500):
        walls = set(rng.sample(cells, int(size * size * 0.12)))
        free = [x for x in cells if x not in walls]
        if not _connected(set(free), size, walls):
            continue
        buchi = rng.choice(free)
        candidates = [
            x for x in free
            if min_frac * size <= abs(x[0] - buchi[0]) + abs(x[1] - buchi[1]) <= max_frac * size
        ]
        if not candidates:
            continue
        reward = rng.choice(candidates)
        start = rng.choice([x for x in free if x not in (buchi, reward)])
        return {
            "name": name,
            "size": size,
            "walls": sorted(walls),
            "buchi": buchi,
            "reward": reward,
            "start": start,
            "category": category,
        }
    raise RuntimeError(f"could not generate grid {name}")


def _digest_int(text: str, digits: int = 12) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:digits], 16)


def build_grids() -> list[dict]:
    grids = []
    for category in ("close", "far"):
        for k in range(TEST_PER_CATEGORY):
            size = 5 + (k % 9)
            seed = _digest_int(f"{_SUITE_SALT}:{category}:{k}")
            grids.append(_generate(seed, size, category, f"{category}_{size}_t{k:03d}"))
    return grids


def rollout_seed(grid: dict, salt: str) -> int:
    return _digest_int(f"{_ROLLOUT_SALT}{salt}:{grid['name']}", 15)


class Sim:
    """Deterministic grid MDP with index-based tables."""

    def __init__(self, grid: dict):
        self.size = grid["size"]
        self.walls = frozenset(tuple(x) for x in grid["walls"])
        self.states = tuple(
            (r, c) for r in range(self.size) for c in range(self.size) if (r, c) not in self.walls
        )
        self.index = {s: i for i, s in enumerate(self.states)}
        self.buchi_cell = tuple(grid["buchi"])
        self.reward_cell = tuple(grid["reward"])
        self.start_cell = tuple(grid["start"])
        self.buchi = self.index[self.buchi_cell]
        self.reward = self.index[self.reward_cell]
        self.succ = [[self.index[self._step(s, a)] for a in range(4)] for s in self.states]
        self.rew = [[(1.0 if self.succ[i][a] == self.reward else 0.0) - 0.01 for a in range(4)]
                    for i in range(len(self.states))]

    def _step(self, state, a):
        dr, dc = DELTAS[a]
        nxt = (state[0] + dr, state[1] + dc)
        if not (0 <= nxt[0] < self.size and 0 <= nxt[1] < self.size) or nxt in self.walls:
            return state
        return nxt


def nominal_policy(sim: Sim) -> list[tuple[float, float, float, float]]:
    """Epsilon-perturbed average-reward optimal policy (relative value iteration)."""
    n = len(sim.states)
    ref = sim.index.get(sim.start_cell, 0)
    bias = [0.0] * n
    for _ in range(500):
        values = [max(sim.rew[s][a] + bias[sim.succ[s][a]] for a in range(4)) for s in range(n)]
        rv = values[ref]
        updated = [v - rv for v in values]
        delta = max(abs(u - b) for u, b in zip(updated, bias))
        bias = updated
        if delta < 1e-10:
            break
    table = []
    for s in range(n):
        q = [sim.rew[s][a] + bias[sim.succ[s][a]] for a in range(4)]
        best = max(q)
        greedy = [a for a in range(4) if abs(q[a] - best) <= 1e-9]
        probs = [NOMINAL_EPSILON / 4.0] * 4
        for a in greedy:
            probs[a] += (1.0 - NOMINAL_EPSILON) / len(greedy)
        table.append(tuple(probs))
    return table


# --------------------------------------------------------------------------
# Guide-facing model (read-only view; the simulator never reads it back)
# --------------------------------------------------------------------------


class GuideModel:
    """What a runtime guide may see: the transition graph, the Buchi region
    and black-box access to the nominal policy. The reward location, the
    instance label and the rollout random numbers are not exposed."""

    __slots__ = ("_size", "_walls", "_states", "_buchi", "_succ", "_nominal")

    def __init__(self, sim: Sim, nominal_views: dict):
        self._size = sim.size
        self._walls = sim.walls
        self._states = sim.states
        self._buchi = frozenset({sim.buchi_cell})
        self._succ = {
            (s, ACTIONS[a]): sim.states[sim.succ[i][a]]
            for i, s in enumerate(sim.states)
            for a in range(4)
        }
        self._nominal = nominal_views

    size = property(lambda self: self._size)
    walls = property(lambda self: self._walls)
    states = property(lambda self: self._states)
    actions = property(lambda self: ACTIONS)
    buchi = property(lambda self: self._buchi)

    def successor(self, state, action):
        return self._succ[(tuple(state), action)]

    def nominal(self, state):
        return self._nominal[tuple(state)]


# --------------------------------------------------------------------------
# Rollouts
# --------------------------------------------------------------------------


class GuideFailure(Exception):
    pass


def _validated(dist) -> list[float]:
    if not isinstance(dist, Mapping):
        raise GuideFailure(f"guide returned {type(dist).__name__}, expected a mapping action->probability")
    probs = [0.0, 0.0, 0.0, 0.0]
    total = 0.0
    for key, value in dist.items():
        idx = ACTION_INDEX.get(key)
        if idx is None:
            raise GuideFailure(f"guide returned unknown action {key!r}")
        try:
            p = float(value)
        except (TypeError, ValueError):
            raise GuideFailure(f"guide returned non-numeric probability {value!r}") from None
        if not (0.0 <= p <= 1.0 + PROB_TOL):  # rejects NaN, inf, negatives
            raise GuideFailure(f"guide returned invalid probability {value!r} for {key!r}")
        probs[idx] += p
        total += p
    if abs(total - 1.0) > PROB_TOL:
        raise GuideFailure(f"guide probabilities sum to {total!r}, expected 1")
    return probs


def _sample(probs, x: float) -> int:
    acc = 0.0
    for a in range(4):
        acc += probs[a]
        if x <= acc:
            return a
    return 3


def run_fixed(sim: Sim, table, nominal, seed: int) -> dict:
    """Fast path for evaluator-owned baselines (stationary policies)."""
    rng = random.Random(seed)
    n = len(sim.states)
    s = rng.randrange(n)
    cdfs = [(p[0], p[0] + p[1], p[0] + p[1] + p[2]) for p in table]
    tvs = [0.5 * sum(abs(p[a] - q[a]) for a in range(4)) for p, q in zip(table, nominal)]
    best = [max(range(4), key=lambda a, q=q: q[a]) for q in nominal]
    succ, rew, buchi = sim.succ, sim.rew, sim.buchi
    visits = overrides = 0
    reward_sum = tv_sum = 0.0
    rand = rng.random
    for _ in range(HORIZON):
        x = rand()
        c0, c1, c2 = cdfs[s]
        a = 0 if x <= c0 else 1 if x <= c1 else 2 if x <= c2 else 3
        tv_sum += tvs[s]
        overrides += a != best[s]
        reward_sum += rew[s][a]
        s = succ[s][a]
        visits += s == buchi
    return {
        "buchi_frequency": visits / HORIZON,
        "average_reward": reward_sum / HORIZON,
        "mean_tv_interference": tv_sum / HORIZON,
        "override_rate": overrides / HORIZON,
    }


def run_guide(sim: Sim, nominal, model: GuideModel, views, guide, seed: int) -> dict:
    rng = random.Random(seed)
    n = len(sim.states)
    s = rng.randrange(n)
    states = sim.states
    succ, rew, buchi = sim.succ, sim.rew, sim.buchi
    best = [max(range(4), key=lambda a, q=q: q[a]) for q in nominal]
    act, observe = guide.act, guide.observe
    visits = overrides = 0
    reward_sum = tv_sum = 0.0
    rand = rng.random
    for _ in range(HORIZON):
        state = states[s]
        nom = nominal[s]
        probs = _validated(act(state, views[state]))
        a = _sample(probs, rand())
        tv_sum += 0.5 * (abs(probs[0] - nom[0]) + abs(probs[1] - nom[1])
                         + abs(probs[2] - nom[2]) + abs(probs[3] - nom[3]))
        overrides += a != best[s]
        r = rew[s][a]
        nxt = succ[s][a]
        reward_sum += r
        visits += nxt == buchi
        observe(state, ACTIONS[a], states[nxt], r)
        s = nxt
    return {
        "buchi_frequency": visits / HORIZON,
        "average_reward": reward_sum / HORIZON,
        "mean_tv_interference": tv_sum / HORIZON,
        "override_rate": overrides / HORIZON,
    }


def _load_factory(spec: dict):
    module_path = (WORKSPACE / spec["module"]).resolve()
    name = f"_factorybot_guide_{hashlib.sha256(str(module_path).encode()).hexdigest()[:10]}"
    loader_spec = importlib.util.spec_from_file_location(name, module_path)
    if loader_spec is None or loader_spec.loader is None:
        raise GuideFailure(f"cannot load guide module {spec['module']!r}")
    module = importlib.util.module_from_spec(loader_spec)
    sys.modules[name] = module
    loader_spec.loader.exec_module(module)
    factory = getattr(module, spec.get("factory", "make_guide"), None)
    if not callable(factory):
        raise GuideFailure(f"guide factory {spec.get('factory', 'make_guide')!r} not found")
    return factory


def _fresh_run(spec: dict, sim: Sim, nominal, budget: float, seed: int) -> dict:
    """Load the guide module from scratch so no state survives between runs."""
    before = set(sys.modules)
    saved_path = list(sys.path)
    try:
        views = {
            s: types.MappingProxyType({ACTIONS[a]: nominal[i][a] for a in range(4)})
            for i, s in enumerate(sim.states)
        }
        model = GuideModel(sim, views)
        factory = _load_factory(spec)
        guide = factory(model, budget, json.loads(json.dumps(spec.get("params", {}))))
        if not (callable(getattr(guide, "act", None)) and callable(getattr(guide, "observe", None))):
            raise GuideFailure("guide object must define act(state, nominal) and observe(...)")
        return run_guide(sim, nominal, model, views, guide, seed)
    finally:
        sys.path[:] = saved_path
        for key in set(sys.modules) - before:
            sys.modules.pop(key, None)


def _baseline_task(task):
    grid, salt = task
    sim = Sim(grid)
    nominal = nominal_policy(sim)
    seed = rollout_seed(grid, salt)
    out = {"instance": grid["name"], "unshielded": run_fixed(sim, nominal, nominal, seed), "naive": {}}
    for lam in NAIVE_MIX_GRID:
        if lam == 0.0:
            out["naive"][lam] = dict(out["unshielded"])
            continue
        table = [tuple((1.0 - lam) * p + lam / 4.0 for p in row) for row in nominal]
        out["naive"][lam] = run_fixed(sim, table, nominal, seed)
    return out


def _method_task(task):
    spec, grid, salt = task
    try:
        if str(WORKSPACE) not in sys.path:
            sys.path.insert(0, str(WORKSPACE))
        sim = Sim(grid)
        nominal = nominal_policy(sim)
        seed = rollout_seed(grid, salt)
        runs = {}
        for budget in BUDGETS:
            runs[budget] = _fresh_run(spec, sim, nominal, budget, seed)
        return {"instance": grid["name"], "ok": True, "runs": runs}
    except GuideFailure as exc:
        return {"instance": grid["name"], "ok": False, "reason": str(exc)}
    except BaseException as exc:  # any crash in submitted code fails the method
        tb = traceback.format_exception_only(type(exc), exc)
        return {"instance": grid["name"], "ok": False, "reason": "guide raised " + "".join(tb).strip()}


# --------------------------------------------------------------------------
# Specs
# --------------------------------------------------------------------------


def discover_specs(guides_dir: Path):
    accepted, rejected = [], []
    if not guides_dir.is_dir():
        return accepted, rejected
    for path in sorted(guides_dir.glob("*.json")):
        try:
            spec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            rejected.append({"file": path.name, "reason": f"unreadable spec: {exc}"})
            continue
        name = spec.get("name", path.stem) if isinstance(spec, dict) else path.stem
        if not isinstance(spec, dict) or not isinstance(spec.get("module"), str):
            rejected.append({"file": path.name, "name": name, "reason": "spec needs a 'module' path"})
            continue
        if not isinstance(name, str) or not name or name.startswith("_") or name in RESERVED_NAMES:
            rejected.append({"file": path.name, "name": name,
                             "reason": "reserved or invalid method name (baselines are evaluator-owned)"})
            continue
        if any(name == other["name"] for other in accepted):
            rejected.append({"file": path.name, "name": name, "reason": "duplicate method name"})
            continue
        accepted.append({
            "name": name,
            "module": spec["module"],
            "factory": spec.get("factory", "make_guide"),
            "params": spec.get("params", {}),
        })
    return accepted, rejected


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def budget_metrics(rows: list[dict], budget: float) -> dict:
    """rows: per instance {freq, reward, nominal_reward, n_states, category, tv, overrides}."""
    within = [r["nominal_reward"] - r["average_reward"] <= budget + 1e-12 for r in rows]
    gated = [r["buchi_frequency"] if w else 0.0 for r, w in zip(rows, within)]
    success = [1.0 if (w and r["buchi_frequency"] >= 1.0 / r["n_states"]) else 0.0
               for r, w in zip(rows, within)]
    kept = [r["buchi_frequency"] for r, w in zip(rows, within) if w]
    return {
        "matched_reward_buchi_frequency": _mean(gated),
        "liveness_success_rate": _mean(success),
        "reward_budget_violation_rate": _mean(0.0 if w else 1.0 for w in within),
        "mean_reward_gap_to_nominal": _mean(r["nominal_reward"] - r["average_reward"] for r in rows),
        "mean_buchi_frequency_ungated": _mean(r["buchi_frequency"] for r in rows),
        "within_budget_mean_buchi_frequency": _mean(kept),
        "average_reward": _mean(r["average_reward"] for r in rows),
        "mean_tv_interference": _mean(r["mean_tv_interference"] for r in rows),
        "override_rate": _mean(r["override_rate"] for r in rows),
    }


def summarize(rows_by_budget: dict, categories: list[str]) -> dict:
    per_budget = {}
    for budget in BUDGETS:
        rows = rows_by_budget[budget]
        entry = {"all": budget_metrics(rows, budget)}
        for cat in categories:
            entry[cat] = budget_metrics([r for r in rows if r["category"] == cat], budget)
        per_budget[budget] = entry
    overall = _mean(per_budget[b]["all"]["matched_reward_buchi_frequency"] for b in BUDGETS)
    by_cat = {
        cat: _mean(per_budget[b][cat]["matched_reward_buchi_frequency"] for b in BUDGETS)
        for cat in categories
    }
    return {
        "matched_reward_buchi_frequency": overall,
        "worst_category_matched_reward_buchi_frequency": min(by_cat.values()),
        "liveness_success_rate": _mean(per_budget[b]["all"]["liveness_success_rate"] for b in BUDGETS),
        "by_category_matched_reward_buchi_frequency": by_cat,
        "per_budget": {f"{b:g}": per_budget[b] for b in BUDGETS},
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def _pool(workers: int):
    ctx = mp.get_context("fork")
    return ctx.Pool(processes=workers, maxtasksperchild=64)


def default_workers() -> int:
    try:
        n = len(os.sched_getaffinity(0))
    except AttributeError:
        n = os.cpu_count() or 1
    return max(1, min(n, 32))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guides-dir", type=Path, default=WORKSPACE / "checkpoints" / "guides")
    parser.add_argument("--output", type=Path, default=WORKSPACE / "scoring" / "scores_test.json")
    parser.add_argument("--workers", type=int, default=default_workers())
    parser.add_argument("--rng-salt", default="", help="noise studies only; the hidden test uses the default")
    parser.add_argument("--rows-out", type=Path, default=None, help="optional per-instance rows (JSONL)")
    args = parser.parse_args()

    grids = build_grids()
    categories = sorted({g["category"] for g in grids})
    n_states = {g["name"]: g["size"] * g["size"] - len(g["walls"]) for g in grids}
    cat_of = {g["name"]: g["category"] for g in grids}
    specs, rejected = discover_specs(args.guides_dir)
    print(f"[eval:{SLICE}] {len(grids)} grids, {len(specs)} guide spec(s), {len(rejected)} rejected, "
          f"{args.workers} worker(s)", flush=True)

    with _pool(args.workers) as pool:
        base = {r["instance"]: r for r in pool.imap_unordered(
            _baseline_task, [(g, args.rng_salt) for g in grids], chunksize=4)}
    nominal_reward = {name: r["unshielded"]["average_reward"] for name, r in base.items()}

    def row(name, run):
        return dict(run, instance=name, category=cat_of[name], n_states=n_states[name],
                    nominal_reward=nominal_reward[name])

    names = sorted(base)
    results, diagnostics, row_dump = {}, {}, []

    # Unshielded nominal policy.
    rows_un = {b: [row(n, base[n]["unshielded"]) for n in names] for b in BUDGETS}
    un = summarize(rows_un, categories)

    # Naive baseline: best global mixing weight per budget (strongest naive).
    naive_rows, naive_choice = {}, {}
    for budget in BUDGETS:
        best = None
        for lam in NAIVE_MIX_GRID:
            rows = [row(n, base[n]["naive"][lam]) for n in names]
            score = budget_metrics(rows, budget)["matched_reward_buchi_frequency"]
            if best is None or score > best[0] + 1e-15:
                best = (score, lam, rows)
        naive_choice[f"{budget:g}"] = best[1]
        naive_rows[budget] = best[2]
    nv = summarize(naive_rows, categories)
    naive_per_budget = {b: nv["per_budget"][f"{b:g}"]["all"]["matched_reward_buchi_frequency"] for b in BUDGETS}
    naive_overall = nv["matched_reward_buchi_frequency"]

    def scored(summary):
        return {
            "matched_reward_buchi_frequency": summary["matched_reward_buchi_frequency"],
            "matched_reward_gain_over_naive": summary["matched_reward_buchi_frequency"] - naive_overall,
            "worst_category_matched_reward_buchi_frequency": summary["worst_category_matched_reward_buchi_frequency"],
            "liveness_success_rate": summary["liveness_success_rate"],
        }

    results["unshielded"] = scored(un)
    results["apply_naive"] = scored(nv)
    diagnostics["unshielded"] = {"status": "ok", "summary": un}
    diagnostics["apply_naive"] = {"status": "ok", "summary": nv, "mix_weight_by_budget": naive_choice}

    for spec in specs:
        print(f"[eval:{SLICE}] scoring guide {spec['name']!r}", flush=True)
        outcome = {}
        failure = None
        pool = _pool(args.workers)
        try:
            for res in pool.imap_unordered(_method_task, [(spec, g, args.rng_salt) for g in grids]):
                if not res["ok"]:
                    failure = f"{res['instance']}: {res['reason']}"
                    break
                outcome[res["instance"]] = res["runs"]
        finally:
            pool.terminate()
            pool.join()
        if failure is not None:
            print(f"[eval:{SLICE}] guide {spec['name']!r} FAILED: {failure}", flush=True)
            results[spec["name"]] = {
                "matched_reward_buchi_frequency": 0.0,
                "matched_reward_gain_over_naive": -naive_overall,
                "worst_category_matched_reward_buchi_frequency": 0.0,
                "liveness_success_rate": 0.0,
            }
            diagnostics[spec["name"]] = {"status": "failed", "reason": failure, "spec": spec}
            continue
        rows = {b: [row(n, outcome[n][b]) for n in names] for b in BUDGETS}
        summary = summarize(rows, categories)
        results[spec["name"]] = scored(summary)
        diagnostics[spec["name"]] = {
            "status": "ok",
            "summary": summary,
            "gain_over_naive_by_budget": {
                f"{b:g}": summary["per_budget"][f"{b:g}"]["all"]["matched_reward_buchi_frequency"] - naive_per_budget[b]
                for b in BUDGETS
            },
            "spec": spec,
        }
        if args.rows_out is not None:
            for b in BUDGETS:
                for r in rows[b]:
                    row_dump.append(dict(r, method=spec["name"], budget=b))

    if args.rows_out is not None:
        for b in BUDGETS:
            for r in rows_un[b]:
                row_dump.append(dict(r, method="unshielded", budget=b))
            for r in naive_rows[b]:
                row_dump.append(dict(r, method="apply_naive", budget=b))
        args.rows_out.parent.mkdir(parents=True, exist_ok=True)
        args.rows_out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in row_dump))

    for name, metrics in results.items():
        for key, value in metrics.items():
            if not math.isfinite(value):  # cannot happen for evaluator-computed values
                raise RuntimeError(f"non-finite metric {name}.{key}")

    payload = {
        "experiments": {
            EXPERIMENT: {"results": results},
            "_diagnostics": {
                "slice": SLICE,
                "horizon": HORIZON,
                "reward_budgets": list(BUDGETS),
                "nominal_epsilon": NOMINAL_EPSILON,
                "instance_count": len(grids),
                "categories": {c: sum(1 for g in grids if g["category"] == c) for c in categories},
                "rng_salt": args.rng_salt,
                "guides_dir": str(args.guides_dir),
                "rejected_specs": rejected,
                "scored_metrics": list(SCORED_METRICS),
                "methods": diagnostics,
            },
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"[eval:{SLICE}] wrote {args.output}", flush=True)


if __name__ == "__main__":
    main()
