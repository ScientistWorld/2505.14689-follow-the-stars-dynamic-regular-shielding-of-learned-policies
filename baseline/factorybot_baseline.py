"""Reference runtime guides for the FactoryBot benchmark.

The scorers compute the two official baselines themselves (``unshielded``
and ``apply_naive``), so their numbers never depend on files a method can
edit. This module exposes the same two behaviours through the runtime-guide
interface so they can be run in the development harness or submitted as
ordinary guides for comparison:

* ``make_identity_guide`` -- returns the nominal distribution unchanged.
* ``make_naive_guide``    -- ApplyNaive: mixes the nominal distribution with
  the uniform distribution (untargeted extra exploration), with mixing
  weight ``params["mix"]`` or ``params["mix_by_budget"][budget]``.
"""

from __future__ import annotations


class IdentityGuide:
    def act(self, state, nominal):
        return dict(nominal)

    def observe(self, state, action, next_state, reward) -> None:
        return None


class NaiveGuide:
    def __init__(self, actions, mix: float):
        self.actions = tuple(actions)
        self.mix = float(mix)

    def act(self, state, nominal):
        u = self.mix / len(self.actions)
        return {a: (1.0 - self.mix) * float(nominal.get(a, 0.0)) + u for a in self.actions}

    def observe(self, state, action, next_state, reward) -> None:
        return None


def make_identity_guide(model, budget, params):
    return IdentityGuide()


def make_naive_guide(model, budget, params):
    table = params.get("mix_by_budget")
    mix = table[f"{budget:g}"] if table else params.get("mix", 0.5)
    return NaiveGuide(model.actions, mix)
