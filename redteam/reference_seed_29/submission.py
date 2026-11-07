"""Audit variant: reference_seed_29."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('reference_seed_29', Path(__file__).resolve().parent)
