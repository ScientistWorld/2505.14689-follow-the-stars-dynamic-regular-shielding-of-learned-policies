"""Restore only files temporarily changed by audit runs."""
from pathlib import Path
import shutil
import json

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "redteam/_state"
for rel in ["checkpoints/factorybot_results.jsonl", "scoring/scores.json",
            "scoring/scores_train.json", "scoring/scores_test.json",
            "data/factorybot_nominal.py", "data/factorybot_suite.json"]:
    source = STATE / rel
    if source.exists():
        shutil.copyfile(source, ROOT / rel)
absent = STATE / "originally_absent.json"
if absent.exists():
    for rel in json.loads(absent.read_text()):
        (ROOT / rel).unlink(missing_ok=True)
