"""Shortcut: shortcut_write_final_scores."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_write_final_scores', Path(__file__).resolve().parent)
