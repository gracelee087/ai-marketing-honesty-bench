"""Repair only the zero-call Sonnet routing attempt; never regenerate completed study outputs."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
target = HERE / "writer_task_sonnet.py"
if target.exists():
    raise RuntimeError("Repair task already prepared")
source = (HERE / "writer_task.py").read_text(encoding="utf-8")
source = source.replace('name="Marketing facts selective validation",', 'name="Marketing facts selective validation Sonnet",')
old = '(getattr(llm, "model", "") or "").endswith(m)'
assert source.count(old) == 1
source = source.replace(old, '(getattr(llm, "model", "") or "").replace("@", "-").endswith(m)')
compile(source, target.name, "exec")
target.write_text(source, encoding="utf-8")
note = {
    "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
    "reason": "Kaggle maps claude-sonnet-5-default to anthropic/claude-sonnet-5@default. The exact-suffix registration guard skipped run 4198882 before any writer or reader call. Its result archive has no results.jsonl and a 0.000203-second duration. That registration-only zero is excluded, not a study result.",
    "change": "Normalize @ to - in the model eligibility guard. Distinct private task; only Sonnet is scheduled. Prompt, briefs, random schedule, reader, caps and analysis are identical to the frozen main study.",
    "parent_freeze_sha256": hashlib.sha256((HERE / "freeze.json").read_bytes()).hexdigest(),
    "task_file": target.name, "task_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    "human_validation": False,
}
(HERE / "freeze_sonnet.json").write_text(json.dumps(note, indent=2) + "\n", encoding="utf-8")
print(json.dumps(note, indent=2))
