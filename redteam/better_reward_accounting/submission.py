"""Audit variant: better_reward_accounting."""
from pathlib import Path
from redteam.case import prepare

def build_submission():
    return prepare('better_reward_accounting', Path(__file__).resolve().parent)
