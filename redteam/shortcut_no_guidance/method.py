"""Shortcut: removing every intervention is a true no-guidance ablation."""

def distribution(state, nominal, available_actions):
    return dict(nominal)
