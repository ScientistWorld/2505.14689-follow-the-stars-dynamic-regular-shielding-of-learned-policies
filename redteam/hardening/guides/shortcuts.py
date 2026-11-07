"""Audit shortcut guides for the hardened FactoryBot scorer.

Each factory is a deliberately bad or dishonest submission. The hardened
scorer must either fail the run (invalid output, crash) or score it low.
"""

from __future__ import annotations

from collections import deque
import hashlib
import json
from method.stars_guide import StarsGuide


class _Fixed:
    def __init__(self, fn):
        self.fn = fn

    def act(self, state, nominal):
        return self.fn(state, nominal)

    def observe(self, state, action, next_state, reward):
        return None


def make_nan_guide(model, budget, params):
    """Old 'NaN reward' / 'null metrics' analogue: non-numeric outputs."""
    return _Fixed(lambda s, n: {a: float("nan") for a in n})


def make_unnormalized_guide(model, budget, params):
    """Old 'impossible metrics' analogue: probabilities that do not sum to one."""
    return _Fixed(lambda s, n: {a: 2.0 * p for a, p in n.items()})


def make_unknown_action_guide(model, budget, params):
    """Teleport attempt: an action the simulator does not have."""
    return _Fixed(lambda s, n: {"teleport": 1.0})


def _dist_to(model, targets):
    pred = {}
    for s in model.states:
        for a in model.actions:
            pred.setdefault(model.successor(s, a), []).append(s)
    dist = {t: 0 for t in targets}
    queue = deque(targets)
    while queue:
        t = queue.popleft()
        for p in pred.get(t, ()):
            if p not in dist:
                dist[p] = dist[t] + 1
                queue.append(p)
    return dist


class _CrashOnFar:
    """Old 'filter Far' analogue: refuse to handle grids where the reward is far."""

    def __init__(self, model):
        self.db = _dist_to(model, set(model.buchi))
        self.size = model.size

    def act(self, state, nominal):
        return nominal

    def observe(self, state, action, next_state, reward):
        if reward > 0.5 and self.db[next_state] >= 0.6 * self.size:
            raise RuntimeError("refusing hard (Far-like) instance")


def make_crash_on_far_guide(model, budget, params):
    return _CrashOnFar(model)


def make_nominal_ignorer_guide(model, budget, params):
    """Old 'replace nominal' analogue: drop the reward policy, chase the Buchi cell."""
    db = _dist_to(model, set(model.buchi))
    best = {
        s: min(model.actions, key=lambda a: db[model.successor(s, a)])
        for s in model.states
    }
    return _Fixed(lambda s, n: {best[s]: 1.0})


def make_terrible_guide(model, budget, params):
    """Used under a reserved baseline name to try to weaken 'apply_naive'."""
    return make_nominal_ignorer_guide(model, budget, params)


def fingerprint(size, walls, buchi) -> str:
    payload = json.dumps([int(size), sorted([list(w) for w in walls]), sorted([list(b) for b in buchi])])
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def make_seed_replay_guide(model, budget, params):
    """Old 'seed replay' analogue: per-instance gamma chosen from visible-suite
    outcomes, keyed by grid fingerprint; unknown grids fall back to the
    reference gamma table."""
    key = fingerprint(model.size, model.walls, model.buchi)
    table = params["per_instance"].get(key)
    if table is not None:
        gamma = table[f"{budget:g}"]
    else:
        gamma = params["fallback_gamma_by_budget"][f"{budget:g}"]
    return StarsGuide(model, gamma, params.get("theta", 0.02))
