"""Audit variant (genuinely better): reward-credit recurring-goal tours.

Port of the iteration-10 red-team "reward accounting" guide to the runtime
guide interface. The guide follows the nominal policy until it has banked
enough reward above a target rate, then makes a complete deterministic tour
to the Buchi cell along shortest paths (ties broken by the nominal), dwells
there, and hands control back to the nominal. The reward cell is not given
to guides; it is discovered from the first observed reward. The allowed
reward loss is derived from the budget the evaluator passes in.
"""

from __future__ import annotations

from collections import deque


def _distances_to(model, targets) -> dict:
    pred: dict = {}
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


class CreditTourGuide:
    def __init__(self, model, budget: float, params: dict):
        self.model = model
        self.actions = tuple(model.actions)
        self.buchi = set(model.buchi)
        self.allowance = max(0.0, float(budget) - float(params.get("margin", 0.05)))
        self.dwell_factor = int(params.get("dwell_factor", 16))
        self.db = _distances_to(model, self.buchi)
        self.progress = {}
        for s in model.states:
            nominal = model.nominal(s)
            best = min(self.db[model.successor(s, a)] for a in self.actions)
            options = [a for a in self.actions if self.db[model.successor(s, a)] == best]
            self.progress[s] = max(options, key=lambda a: nominal[a])
        self.reward_cell = None
        self.phase = "nominal"
        self.dwell_left = 0
        self.credit = 0.0
        self.target = 0.0
        self.reserve = float("inf")
        self.dwell = 0

    def _discover(self, cell) -> None:
        self.reward_cell = cell
        can_stay = any(self.model.successor(cell, a) == cell for a in self.actions)
        upper = (1.0 if can_stay else 0.5) - 0.01
        self.target = upper - self.allowance
        back = _distances_to(self.model, {cell})
        buchi = next(iter(self.buchi))
        self.dwell = self.dwell_factor * max(1, self.db[cell])
        self.reserve = self.target * (self.db[cell] + self.dwell + back[buchi]) + 10.0

    def act(self, state, nominal):
        if self.reward_cell is not None:
            if self.phase == "nominal" and state == self.reward_cell and self.credit >= self.reserve:
                self.phase = "outbound"
            if self.phase == "outbound" and state in self.buchi:
                self.phase = "dwell"
                self.dwell_left = self.dwell
        if self.phase == "nominal":
            return nominal
        action = self.progress[state]
        if self.phase == "dwell":
            self.dwell_left -= 1
            if self.dwell_left <= 0:
                self.phase = "nominal"
        return {action: 1.0}

    def observe(self, state, action, next_state, reward) -> None:
        if self.reward_cell is None and reward > 0.5:
            self._discover(next_state)
        if self.reward_cell is not None:
            self.credit += reward - self.target


def make_guide(model, budget, params):
    return CreditTourGuide(model, budget, params)
