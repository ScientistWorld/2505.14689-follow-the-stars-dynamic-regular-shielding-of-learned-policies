"""Shortcut: shortcut_train_selection."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('shortcut_train_selection', Path(__file__).resolve().parent)
