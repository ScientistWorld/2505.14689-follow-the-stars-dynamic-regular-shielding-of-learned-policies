"""ApplySTARs as a FactoryBot runtime guide.

The guide synthesizes the Buchi strategy template for the instance's
transition graph (ReachTemplate specialization of ParityTemplate, see
``template_synthesis.py``) and post-shields the nominal action distribution
with Definition 2 (``stars.py``). The enforcement parameter gamma is chosen
per reward budget from a table fixed before evaluation (tuned on the visible
train suite by ``factorybot_method.py``); theta is the threshold of (1a).
"""

from __future__ import annotations

from method.stars import StarShield, StrategyTemplate
from method.template_synthesis import synthesize_buchi_reach_template

DEFAULT_THETA = 0.02


class StarsGuide:
    def __init__(self, model, gamma: float, theta: float = DEFAULT_THETA,
                 template: StrategyTemplate | None = None):
        self.template = template if template is not None else synthesize_buchi_reach_template(model, model.buchi)
        self.shield = StarShield(self.template, gamma=float(gamma), theta=float(theta))
        self.actions = tuple(model.actions)

    def act(self, state, nominal):
        return self.shield.distribution(state, nominal, self.actions)

    def observe(self, state, action, next_state, reward) -> None:
        self.shield.observe(state, action)


def gamma_for_budget(params: dict, budget: float) -> float:
    table = params["gamma_by_budget"]
    return float(table[f"{budget:g}"])


def make_guide(model, budget: float, params: dict) -> StarsGuide:
    return StarsGuide(model, gamma_for_budget(params, budget), float(params.get("theta", DEFAULT_THETA)))
