"""Build private Kaggle task sources, run offline checks, then freeze before any requests."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(revision=False):
    if (HERE / "freeze.json").exists() and not revision:
        raise RuntimeError("Study is frozen; do not silently rebuild. Record a deviation for any new version.")
    companies = json.loads((HERE / "companies.json").read_text(encoding="utf-8"))
    original = ast.parse((ROOT / "benchmark" / "marketing_honesty.py").read_text(encoding="utf-8"))
    judge_prompt = next(ast.literal_eval(n.value) for n in original.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "JUDGE_PROMPT" for t in n.targets))
    header = "# Frozen held-out follow-up; no human validation.\n"
    header += "COMPANIES = " + repr(companies) + "\nJUDGE_PROMPT = " + repr(judge_prompt) + "\n"
    header += "DATA_SHA256 = " + repr(sha(HERE / "companies.json")) + "\n"
    header += "PROTOCOL_SHA256 = " + repr(sha(HERE / "PROTOCOL.md")) + "\n"
    header += "WRITER_MODELS = " + repr(["gpt-5.4-2026-03-05", "gpt-5.4-nano-2026-03-17", "gemini-3.8-flash", "claude-sonnet-5-default"]) + "\n"
    common = header + (HERE / "engine.py").read_text(encoding="utf-8") + "\n" + (HERE / "task_runtime.py").read_text(encoding="utf-8")
    writer = common + '''
@kbench.task(name="Marketing facts selective validation", description="Held-out cold emails under baseline, facts-only and selective-use instructions. Score is reader-clean share, not human-rated quality.")
def marketing_facts_selective_validation(llm) -> float:
    # Registration executes the notebook using a platform-selected model.
    # Do not spend quota or mix that unplanned model into the frozen study.
    if not any((getattr(llm, "model", "") or "").endswith(m) for m in WRITER_MODELS):
        print("Registration only: model is outside the frozen four-writer study; no calls made.")
        return 0.0
    data = pd.DataFrame(schedule(COMPANIES))
    with kbench.client.enable_cache():
        runs = heldout_email.evaluate(llm=[llm], evaluation_data=data, n_jobs=2,
                                     timeout=900, on_failure="continue", max_attempts=1)
    records = save_runs(runs, len(data), "writer")
    scored = [r for r in records if r.get("reader") is not None]
    if not scored:
        raise RuntimeError("No reader-scored outputs; score undefined")
    return sum(r["reader"]["total"] == 0 for r in scored) / len(scored)

# %% [run]
marketing_facts_selective_validation.run(kbench.llm)
'''
    control = common + '''
@kbench.task(name="Marketing reader synthetic controls", description="Thirty known-construction controls for the marketing reader; automatic checks, not human validation.")
def marketing_reader_synthetic_controls(llm) -> float:
    if not (getattr(llm, "model", "") or "").endswith("glm-5"):
        print("Registration only: controls must be explicitly run with glm-5; no calls made.")
        return 0.0
    data = pd.DataFrame([{"company_id": c["id"], "kind": kind} for c in COMPANIES
                         for kind in ["supported", "wrong_price", "wrong_team"]])
    with kbench.client.enable_cache():
        runs = heldout_reader_control.evaluate(llm=[llm], evaluation_data=data, n_jobs=2,
                                              timeout=900, on_failure="continue", max_attempts=1)
    records = save_runs(runs, len(data), "controls")
    scored = [r for r in records if r.get("pass") is not None]
    if not scored:
        raise RuntimeError("No scored controls; score undefined")
    return sum(r["pass"] for r in scored) / len(scored)

# %% [run]
marketing_reader_synthetic_controls.run(kbench.llm)
'''
    for name, source in [("writer_task.py", writer), ("control_task.py", control)]:
        compile(source, name, "exec")
        (HERE / name).write_text(source, encoding="utf-8")
    print("Built standalone tasks; no model calls made.")


def freeze(revision=False):
    if (HERE / "freeze.json").exists() and not revision:
        raise RuntimeError("Already frozen")
    names = ["PROTOCOL.md", "companies.json", "engine.py", "task_runtime.py", "writer_task.py", "control_task.py", "analyze.py", "test_study.py"]
    manifest = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(), "human_validation": False,
                "writer_models": ["gpt-5.4-2026-03-05", "gpt-5.4-nano-2026-03-17", "gemini-3.8-flash", "claude-sonnet-5-default"],
                "files": {name: sha(HERE / name) for name in names}}
    (HERE / "freeze.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--registration-revision", action="store_true")
    args = ap.parse_args()
    if args.registration_revision:
        import shutil
        history = HERE / "history" / "registration_v1"
        if history.exists() or (HERE / "receipts" / "writer_launch.json").exists():
            raise RuntimeError("This one-time pre-run correction cannot be repeated or used after launching models")
        old = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
        history.mkdir(parents=True)
        for name in ["freeze.json", *old["files"]]:
            # Preserve the exact v1 task uploaded to Kaggle; task source contains its original runtime.
            shutil.copy2(HERE / name, history / name)
        build(revision=True)
        freeze(revision=True)
    elif args.freeze:
        freeze()
    else:
        build()
