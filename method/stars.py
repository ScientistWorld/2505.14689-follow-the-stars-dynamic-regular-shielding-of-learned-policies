"""Strategy-Template-based Adaptive Runtime Shielding (STARs).

This implements the paper's Definition 2 for finite grid MDPs: unsafe actions
are removed, co-live actions are penalized by history counters, and live-group
actions are boosted by history counters before thresholding and normalization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


State = tuple[int, int]
Action = str
Edge = tuple[State, Action]


@dataclass(frozen=True)
class StrategyTemplate:
    unsafe: frozenset[Edge] = frozenset()
    colive: frozenset[Edge] = frozenset()
    live_groups: tuple[frozenset[Edge], ...] = ()


@dataclass
class StarShield:
    template: StrategyTemplate
    gamma: float
    theta: float
    colive_counts: dict[Edge, int] = field(default_factory=dict)
    live_counts: dict[int, int] = field(default_factory=dict)
    _edge_to_live_group: dict[Edge, int] = field(default_factory=dict, init=False, repr=False)
    _edge_to_live_groups: dict[Edge, list[int]] = field(default_factory=dict, init=False, repr=False)
    _live_group_sources: dict[int, frozenset[State]] = field(default_factory=dict, init=False, repr=False)
    _state_groups: dict[State, tuple[int, ...]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        state_groups: dict[State, list[int]] = {}
        for idx, group in enumerate(self.template.live_groups):
            self._live_group_sources[idx] = frozenset(state for state, _ in group)
            for state in self._live_group_sources[idx]:
                state_groups.setdefault(state, []).append(idx)
            for edge in group:
                self._edge_to_live_groups.setdefault(edge, []).append(idx)
                if edge not in self._edge_to_live_group:
                    self._edge_to_live_group[edge] = idx
        self._state_groups = {state: tuple(groups) for state, groups in state_groups.items()}

    def distribution(
        self,
        state: State,
        nominal: Mapping[Action, float],
        available_actions: tuple[Action, ...],
    ) -> dict[Action, float]:
        """Definition 2: (1b) counter-based reweighting, then (1a) threshold and normalize."""
        unsafe = self.template.unsafe
        colive = self.template.colive
        gamma = self.gamma
        adjusted: list[float] = []
        total = 0.0
        for action in available_actions:
            edge = (state, action)
            value = float(nominal.get(action, 0.0))
            if edge in unsafe:
                value = 0.0
            elif edge in colive:
                value -= gamma * self.colive_counts.get(edge, 0)
            else:
                live_group = self._edge_to_live_group.get(edge)
                if live_group is not None:
                    value += gamma * self.live_counts.get(live_group, 0)
            if value < 0.0:
                value = 0.0
            adjusted.append(value)
            total += value

        if total <= 0.0:
            first = [1.0 / len(adjusted)] * len(adjusted)
        else:
            first = [v / total for v in adjusted]
        theta = self.theta
        thresholded = [p if p > theta else 0.0 for p in first]
        mass = 0.0
        for p in thresholded:
            mass += p
        if mass <= 0.0:
            # Degenerate only when the nominal policy put all mass on removed
            # actions. The paper suggests epsilon perturbation for this case.
            return normalize({a: 1.0 for a in available_actions if (state, a) not in unsafe})
        return {a: p / mass for a, p in zip(available_actions, thresholded)}

    def observe(self, state: State, action: Action) -> None:
        edge = (state, action)
        if edge in self.template.colive:
            self.colive_counts[edge] = self.colive_counts.get(edge, 0) + 1

        # Definition 1: count_H is the number of visits to src(H) since an
        # edge of H was last taken. Only groups with `state` in src(H) can
        # change (an edge of H always starts in src(H)), so we touch those.
        live_groups = self._edge_to_live_groups.get(edge, ())
        for idx in self._state_groups.get(state, ()):
            if idx in live_groups:
                self.live_counts[idx] = 0
            else:
                self.live_counts[idx] = self.live_counts.get(idx, 0) + 1


def normalize(values: Mapping[Action, float]) -> dict[Action, float]:
    total = sum(max(v, 0.0) for v in values.values())
    if total <= 0.0:
        n = len(values)
        return {k: 1.0 / n for k in values}
    return {k: max(v, 0.0) / total for k, v in values.items()}


def total_variation(p: Mapping[Action, float], q: Mapping[Action, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(float(p.get(k, 0.0)) - float(q.get(k, 0.0))) for k in keys)
