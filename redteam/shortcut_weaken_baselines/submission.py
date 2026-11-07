"""Shortcut: shortcut_weaken_baselines."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_weaken_baselines', Path(__file__).resolve().parent)
