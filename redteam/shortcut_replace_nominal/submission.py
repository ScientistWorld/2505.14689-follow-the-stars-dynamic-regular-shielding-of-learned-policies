"""Shortcut: shortcut_replace_nominal."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_replace_nominal', Path(__file__).resolve().parent)
