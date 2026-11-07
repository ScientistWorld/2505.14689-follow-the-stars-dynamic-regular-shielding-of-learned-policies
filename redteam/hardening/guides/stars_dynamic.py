"""Audit variant (better, inside the paper's framework): dynamic-gamma STARs.

Same strategy template and Definition 2 shield as the reference, but the
enforcement parameter is changed at runtime (Sec. 3.1 / Remark 11 of the
paper): gamma_high while the realized average reward stays above
``nominal - safety * budget``, and gamma = 0 (the thresholded nominal)
whenever the run falls behind. The nominal's expected average reward is
computed from the model once the reward cell has been observed.
"""

from __future__ import annotations

from method.stars import StarShield
from method.template_synthesis import synthesize_buchi_reach_template


class DynamicStarsGuide:
    def __init__(self, model, budget: float, params: dict):
        self.model = model
        self.actions = tuple(model.actions)
        self.budget = float(budget)
        self.gamma_high = float(params.get("gamma_high", 1.0))
        self.safety = float(params.get("safety", 0.8))
        template = synthesize_buchi_reach_template(model, model.buchi)
        self.shield = StarShield(template, gamma=0.0, theta=float(params.get("theta", 0.02)))
        self.t = 0
        self.reward_sum = 0.0
        self.r_nom = None

    def _nominal_average_reward(self, cell) -> float:
        states = self.model.states
        index = {s: i for i, s in enumerate(states)}
        trans = []
        for s in states:
            nominal = self.model.nominal(s)
            trans.append([(index[self.model.successor(s, a)], nominal[a]) for a in self.actions])
        n = len(states)
        pi = [1.0 / n] * n
        acc = [0.0] * n
        for it in range(400):
            nxt = [0.0] * n
            for i, row in enumerate(trans):
                w = pi[i]
                if w:
                    for j, p in row:
                        nxt[j] += w * p
            pi = nxt
            if it >= 200:
                for i in range(n):
                    acc[i] += pi[i]
        total = sum(acc)
        reward = 0.0
        for i, s in enumerate(states):
            nominal = self.model.nominal(s)
            for a in self.actions:
                hit = 1.0 if self.model.successor(s, a) == cell else 0.0
                reward += acc[i] / total * nominal[a] * (hit - 0.01)
        return reward

    def act(self, state, nominal):
        if self.r_nom is None:
            gamma = 0.0
        else:
            allowed = self.t * (self.r_nom - self.safety * self.budget)
            gamma = self.gamma_high if self.reward_sum >= allowed else 0.0
        self.shield.gamma = gamma
        return self.shield.distribution(state, nominal, self.actions)

    def observe(self, state, action, next_state, reward) -> None:
        self.shield.observe(state, action)
        self.t += 1
        self.reward_sum += reward
        if self.r_nom is None and reward > 0.5:
            self.r_nom = self._nominal_average_reward(next_state)


def make_guide(model, budget, params):
    return DynamicStarsGuide(model, budget, params)
