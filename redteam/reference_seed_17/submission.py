"""Audit variant: reference_seed_17."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('reference_seed_17', Path(__file__).resolve().parent)
