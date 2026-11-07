"""Shortcut: shortcut_seed_replay."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_seed_replay', Path(__file__).resolve().parent)
