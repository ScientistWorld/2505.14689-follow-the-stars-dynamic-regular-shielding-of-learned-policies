"""Audit variant: reference_original."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('reference_original', Path(__file__).resolve().parent)
