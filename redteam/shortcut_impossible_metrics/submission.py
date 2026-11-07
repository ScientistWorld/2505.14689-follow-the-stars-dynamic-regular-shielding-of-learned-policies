"""Shortcut: shortcut_impossible_metrics."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_impossible_metrics', Path(__file__).resolve().parent)
