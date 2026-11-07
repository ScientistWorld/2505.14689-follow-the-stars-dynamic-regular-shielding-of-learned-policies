"""Create reversible per-workspace snapshots before running the audit."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "redteam/_state"
STATE.mkdir(exist_ok=True)
absent = []
for rel in ["scripts/run.sh", "checkpoints/factorybot_results.jsonl", "scoring/scores.json",
            "scoring/scores_train.json", "scoring/scores_test.json", "scoring/reference.json",
            "data/factorybot_nominal.py", "data/factorybot_suite.json"]:
    target = STATE / rel
    source = ROOT / rel
    if not target.exists():
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        else:
            absent.append(rel)
if not (STATE / "originally_absent.json").exists():
    (STATE / "originally_absent.json").write_text(json.dumps(absent))
