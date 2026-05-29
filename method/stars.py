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

    def distribution(
        self,
        state: State,
        nominal: Mapping[Action, float],
        available_actions: tuple[Action, ...],
    ) -> dict[Action, float]:
        adjusted: dict[Action, float] = {}
        for action in available_actions:
            edge = (state, action)
            value = float(nominal.get(action, 0.0))
            if edge in self.template.unsafe:
                value = 0.0
            elif edge in self.template.colive:
                value -= self.gamma * self.colive_counts.get(edge, 0)
            else:
                for idx, group in enumerate(self.template.live_groups):
                    if edge in group:
                        value += self.gamma * self.live_counts.get(idx, 0)
                        break
            adjusted[action] = max(value, 0.0)

        first = normalize(adjusted)
        thresholded = {a: (p if p > self.theta else 0.0) for a, p in first.items()}
        if sum(thresholded.values()) <= 0.0:
            # Degenerate only when the nominal policy put all mass on removed
            # actions. The paper suggests epsilon perturbation for this case.
            thresholded = {a: 1.0 for a in available_actions if (state, a) not in self.template.unsafe}
        return normalize(thresholded)

    def observe(self, state: State, action: Action) -> None:
        edge = (state, action)
        if edge in self.template.colive:
            self.colive_counts[edge] = self.colive_counts.get(edge, 0) + 1

        for idx, group in enumerate(self.template.live_groups):
            sources = {s for s, _ in group}
            if edge in group:
                self.live_counts[idx] = 0
            elif state in sources:
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

