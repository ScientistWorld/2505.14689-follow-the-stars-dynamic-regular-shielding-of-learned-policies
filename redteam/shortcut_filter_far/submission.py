"""Shortcut: shortcut_filter_far."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_filter_far', Path(__file__).resolve().parent)
