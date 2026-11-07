"""Shortcut: shortcut_drop_baselines."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_drop_baselines', Path(__file__).resolve().parent)
