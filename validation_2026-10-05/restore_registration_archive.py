"""Restore archived common files from the exact uploaded v1 source and verify original hashes."""
import hashlib
import json
from pathlib import Path

history = Path(__file__).resolve().parent / "history" / "registration_v1"
manifest = json.loads((history / "freeze.json").read_text(encoding="utf-8"))
source = (history / "writer_task.py").read_text(encoding="utf-8")
runtime = source.split('"""Appended to frozen constants and engine.py for the standalone Kaggle tasks."""', 1)[1]
runtime = '"""Appended to frozen constants and engine.py for the standalone Kaggle tasks."""' + runtime.split('\n@kbench.task(name="Marketing facts selective validation"', 1)[0]
runtime = runtime.rstrip() + "\n"
protocol = (history / "PROTOCOL.md").read_text(encoding="utf-8").split("\n## Registration correction before the planned model runs", 1)[0].rstrip() + "\n"
for name, text in [("task_runtime.py", runtime), ("PROTOCOL.md", protocol)]:
    assert hashlib.sha256(text.encode()).hexdigest() == manifest["files"][name], name
    (history / name).write_bytes(text.encode("utf-8"))
for name, expected in manifest["files"].items():
    assert hashlib.sha256((history / name).read_bytes()).hexdigest() == expected, name
print("Archived v1 inputs match every hash in the original pre-registration manifest.")
