"""Shortcut: shortcut_nan_reward."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_nan_reward', Path(__file__).resolve().parent)
