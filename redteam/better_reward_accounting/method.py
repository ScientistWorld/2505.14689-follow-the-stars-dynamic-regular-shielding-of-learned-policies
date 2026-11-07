"""A genuine runtime guide: fund recurring-goal excursions with reward credit.

The reward-only nominal policy remains unchanged. We spend a conservative
per-instance reward-loss allowance on complete tours rather than reacting
to reward debt halfway along a path. All configuration choices are global;
the visible evaluator selects the budget on development instances.
"""
from __future__ import annotations

import random
from data.factorybot import ACTIONS, shortest_distances


def run_episode(instance, nominal_policy, steps, seed, budget):
    rng = random.Random(seed)
    state = rng.choice(list(instance.states))
    db = shortest_distances(instance, instance.buchi)
    dr = shortest_distances(instance, instance.reward)
    # Deterministic-grid upper bound on ANY nominal reward: an interior
    # reward cell requires leaving between visits; a blocked action can stay.
    can_stay = any(instance.step(instance.reward, a) == instance.reward for a in ACTIONS)
    reward_upper = (1.0 if can_stay else 0.5) - 0.01
    target = reward_upper - budget
    dwell = 16 * max(1, db[instance.reward])
    reserve = target * (db[instance.reward] + dwell + dr[instance.buchi]) + 10.0
    next_state = {(s, a): instance.step(s, a) for s in instance.states for a in ACTIONS}
    progress_action = {}
    for s in instance.states:
        best_dist = min(db[next_state[s, a]] for a in ACTIONS)
        candidates = [a for a in ACTIONS if db[next_state[s, a]] == best_dist]
        progress_action[s] = max(candidates, key=lambda a: nominal_policy[s][a])
    phase = "nominal"
    dwell_left = 0
    credit = 0.0
    visits = reward_hits = overrides = 0
    tv_sum = 0.0
    for _ in range(steps):
        nominal = nominal_policy[state]
        if phase == "nominal" and state == instance.reward and credit >= reserve:
            phase = "outbound"
        if phase == "outbound" and state == instance.buchi:
            phase, dwell_left = "dwell", dwell
        if phase == "nominal":
            x, acc = rng.random(), 0.0
            action = ACTIONS[-1]
            for a in ACTIONS:
                acc += nominal[a]
                if x <= acc:
                    action = a
                    break
        else:
            # A deterministic post-processing decision, with ties decided
            # by the fixed nominal action probabilities.
            action = progress_action[state]
            tv_sum += 1.0 - nominal[action]
            if phase == "dwell":
                dwell_left -= 1
                if dwell_left <= 0:
                    phase = "nominal"
        overrides += action != max(nominal, key=nominal.get)
        state = next_state[state, action]
        hit = int(state == instance.reward)
        reward_hits += hit
        credit += hit - 0.01 - target
        visits += state == instance.buchi
    return {
        "instance": instance.name, "category": instance.category,
        "method": "apply_stars", "steps": steps, "gamma": None,
        "theta": None, "config": f"reward_credit_{budget}",
        "buchi_frequency": visits / steps,
        "average_reward": reward_hits / steps - 0.01,
        "mean_tv_interference": tv_sum / steps,
        "override_rate": overrides / steps,
        "nominal_policy": "relative_value_iteration_average_reward",
    }
