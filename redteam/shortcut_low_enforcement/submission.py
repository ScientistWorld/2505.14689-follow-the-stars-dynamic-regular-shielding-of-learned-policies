"""Shortcut: shortcut_low_enforcement."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_low_enforcement', Path(__file__).resolve().parent)
