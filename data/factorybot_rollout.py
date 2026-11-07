"""Public development harness mirroring the FactoryBot evaluation protocol.

A runtime guide is any object with

    act(state, nominal) -> {action: probability}
    observe(state, action, next_state, reward) -> None

built by a factory ``make_guide(model, budget, params)``. ``model`` exposes
the transition graph (``size``, ``walls``, ``states``, ``actions``,
``successor(state, action)``), the Buchi region (``buchi``), and black-box
queries of the nominal policy (``nominal(state)``). The reward location and
the instance's Close/Far label are not exposed.

The functions here reproduce the scorer's rollout semantics (random start
state, canonical action order for sampling, reward, Buchi-visit counting) so
methods can be developed and tuned on the visible suite. They are not used
by the scorers, which carry their own private copies.
"""

from __future__ import annotations

from collections.abc import Mapping
import importlib.util
import json
from pathlib import Path
import random
import types

from data.factorybot import ACTIONS, FactoryBotInstance

HORIZON = 100_000
BUDGETS = (0.1, 0.2, 0.3, 0.4)

PolicyTable = dict[tuple[int, int], dict[str, float]]


class GuideModel:
    """Read-only view of an instance, as handed to a runtime guide."""

    def __init__(self, instance: FactoryBotInstance, nominal_policy: PolicyTable):
        self._instance = instance
        self._states = instance.states
        self._views = {
            s: types.MappingProxyType({a: float(nominal_policy[s][a]) for a in ACTIONS})
            for s in self._states
        }

    @property
    def size(self) -> int:
        return self._instance.size

    @property
    def walls(self) -> frozenset:
        return self._instance.walls

    @property
    def states(self) -> tuple:
        return self._states

    @property
    def actions(self) -> tuple:
        return ACTIONS

    @property
    def buchi(self) -> frozenset:
        return frozenset({self._instance.buchi})

    def successor(self, state, action):
        return self._instance.step(tuple(state), action)

    def nominal(self, state):
        return self._views[tuple(state)]


_ACTION_INDEX = {a: i for i, a in enumerate(ACTIONS)}


def _probs(dist) -> list[float]:
    if not isinstance(dist, Mapping):
        raise ValueError(f"guide returned {type(dist).__name__}, expected a mapping")
    probs = [0.0, 0.0, 0.0, 0.0]
    total = 0.0
    for key, value in dist.items():
        idx = _ACTION_INDEX.get(key)
        p = float(value)
        if idx is None or not (0.0 <= p <= 1.0 + 1e-6):
            raise ValueError(f"invalid guide output {key!r}: {value!r}")
        probs[idx] += p
        total += p
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"guide probabilities sum to {total!r}")
    return probs


def _sample(probs, x: float) -> int:
    acc = 0.0
    for idx, p in enumerate(probs):
        acc += p
        if x <= acc:
            return idx
    return len(probs) - 1


def rollout_guide(
    instance: FactoryBotInstance,
    nominal_policy: PolicyTable,
    guide,
    *,
    steps: int = HORIZON,
    seed: int = 7,
) -> dict:
    """Run one guide from a random start state, as the scorers do."""

    rng = random.Random(seed)
    states = list(instance.states)
    index = {s: i for i, s in enumerate(states)}
    succ = [[index[instance.step(s, a)] for a in ACTIONS] for s in states]
    rew = [[instance.reward_value(s, a) for a in ACTIONS] for s in states]
    buchi = index[instance.buchi]
    nominal = [[float(nominal_policy[s][a]) for a in ACTIONS] for s in states]
    views = {s: types.MappingProxyType(dict(nominal_policy[s])) for s in states}
    act, observe, rand = guide.act, guide.observe, rng.random
    s = rng.randrange(len(states))
    visits = 0
    reward_sum = 0.0
    tv_sum = 0.0
    for _ in range(steps):
        state = states[s]
        nom = nominal[s]
        probs = _probs(act(state, views[state]))
        a = _sample(probs, rand())
        tv_sum += 0.5 * (abs(probs[0] - nom[0]) + abs(probs[1] - nom[1])
                         + abs(probs[2] - nom[2]) + abs(probs[3] - nom[3]))
        r = rew[s][a]
        nxt = succ[s][a]
        reward_sum += r
        visits += nxt == buchi
        observe(state, ACTIONS[a], states[nxt], r)
        s = nxt
    return {
        "buchi_frequency": visits / steps,
        "average_reward": reward_sum / steps,
        "mean_tv_interference": tv_sum / steps,
    }


def rollout_policy(
    instance: FactoryBotInstance,
    policy: PolicyTable,
    *,
    steps: int = HORIZON,
    seed: int = 7,
) -> dict:
    """Fast rollout of a stationary policy (e.g. the unshielded nominal)."""

    rng = random.Random(seed)
    states = list(instance.states)
    index = {s: i for i, s in enumerate(states)}
    succ = [[index[instance.step(s, a)] for a in ACTIONS] for s in states]
    rew = [[(1.0 if states[succ[i][k]] == instance.reward else 0.0) - 0.01 for k in range(4)] for i in range(len(states))]
    cdfs = []
    for s in states:
        p = [policy[s][a] for a in ACTIONS]
        cdfs.append((p[0], p[0] + p[1], p[0] + p[1] + p[2]))
    buchi = index[instance.buchi]
    s = rng.randrange(len(states))
    visits = 0
    reward_sum = 0.0
    for _ in range(steps):
        x = rng.random()
        c0, c1, c2 = cdfs[s]
        a = 0 if x <= c0 else 1 if x <= c1 else 2 if x <= c2 else 3
        reward_sum += rew[s][a]
        s = succ[s][a]
        visits += s == buchi
    return {"buchi_frequency": visits / steps, "average_reward": reward_sum / steps}


def load_spec(path: Path, root: Path | None = None):
    """Return (factory, params) for a guide spec JSON (same format the scorers read)."""

    spec = json.loads(Path(path).read_text())
    root = root or Path(__file__).resolve().parents[1]
    module_path = (root / spec["module"]).resolve()
    loader = importlib.util.spec_from_file_location(f"_dev_guide_{module_path.stem}", module_path)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return getattr(module, spec.get("factory", "make_guide")), spec.get("params", {})
