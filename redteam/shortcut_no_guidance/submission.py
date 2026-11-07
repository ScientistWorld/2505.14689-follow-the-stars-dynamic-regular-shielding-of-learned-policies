"""Shortcut: shortcut_no_guidance."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_no_guidance', Path(__file__).resolve().parent)
