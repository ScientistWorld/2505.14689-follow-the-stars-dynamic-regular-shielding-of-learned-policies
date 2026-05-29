"""Strategy-template synthesis for the FactoryBot Büchi setting.

The paper's STARs pipeline first computes a winning strategy template and then
uses Definition 2 to post-shield a nominal policy. For Büchi objectives in a
strongly connected finite MDP, the ParityTemplate construction reduces to the
ReachTemplate case described in the appendix: partition states by attractor
layers Q_0, Q_1, ... with Q_0 equal to the accepting set, and add live groups
containing edges from Q_i to Q_{i-1}.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping

from data.factorybot import ACTIONS, FactoryBotInstance
from method.stars import Edge, State, StrategyTemplate


def synthesize_buchi_reach_template(
    instance: FactoryBotInstance,
    accepting: Iterable[State],
) -> StrategyTemplate:
    """Compute the Büchi live-group template for a deterministic grid MDP.

    This is the Büchi/ReachTemplate specialization of ParityTemplate for the
    FactoryBot setting: all states in the generated grids are in one strongly
    connected winning region, so the template has no unsafe or co-live edges
    and its live groups enforce recurring progress back to the accepting set.
    """

    layers = attractor_layers(instance, set(accepting))
    if len(layers) <= 1:
        return StrategyTemplate()

    state_to_layer = {
        state: layer_idx
        for layer_idx, layer in layers.items()
        for state in layer
    }
    unreachable = set(instance.states) - set(state_to_layer)
    unsafe = _unsafe_edges(instance, unreachable)

    live_groups: list[frozenset[Edge]] = []
    for layer_idx in range(1, max(layers) + 1):
        edges = []
        for state in layers[layer_idx]:
            for action in ACTIONS:
                successor = instance.step(state, action)
                if state_to_layer.get(successor, 10**9) < layer_idx:
                    edges.append((state, action))
        if edges:
            live_groups.append(frozenset(edges))

    return StrategyTemplate(
        unsafe=frozenset(unsafe),
        colive=frozenset(),
        live_groups=tuple(live_groups),
    )


def attractor_layers(
    instance: FactoryBotInstance,
    target_states: set[State],
) -> dict[int, set[State]]:
    """Return attractor partitions Q_i for deterministic reachability."""

    layers: dict[int, set[State]] = {0: set(target_states)}
    state_to_layer: dict[State, int] = {state: 0 for state in target_states}
    queue: deque[State] = deque(target_states)

    while queue:
        state = queue.popleft()
        current_layer = state_to_layer[state]
        for predecessor, action in predecessors(instance, state):
            if predecessor in state_to_layer:
                continue
            state_to_layer[predecessor] = current_layer + 1
            layers.setdefault(current_layer + 1, set()).add(predecessor)
            queue.append(predecessor)

    return layers


def predecessors(instance: FactoryBotInstance, state: State) -> Iterable[tuple[State, str]]:
    for candidate in instance.states:
        for action in ACTIONS:
            if instance.step(candidate, action) == state:
                yield candidate, action


def _unsafe_edges(instance: FactoryBotInstance, unreachable: set[State]) -> set[Edge]:
    unsafe: set[Edge] = set()
    if not unreachable:
        return unsafe
    winning = set(instance.states) - unreachable
    for state in winning:
        for action in ACTIONS:
            if instance.step(state, action) not in winning:
                unsafe.add((state, action))
    for state in unreachable:
        for action in ACTIONS:
            unsafe.add((state, action))
    return unsafe


def template_summary(template: StrategyTemplate) -> Mapping[str, int]:
    return {
        "unsafe_edges": len(template.unsafe),
        "colive_edges": len(template.colive),
        "live_groups": len(template.live_groups),
        "live_edges": sum(len(group) for group in template.live_groups),
    }
