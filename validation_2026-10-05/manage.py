"""Manage only the two frozen private follow-up tasks; never publishes or buys credits."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

HERE = Path(__file__).resolve().parent
TASKS = {"writer": ("marketing-facts-selective-validation", "writer_task.py"),
         "controls": ("marketing-reader-synthetic-controls", "control_task.py"),
         "sonnet": ("marketing-facts-selective-validation-sonnet", "writer_task_sonnet.py")}


def verify():
    manifest = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Frozen input changed: {name}")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["push", "status", "progress", "launch", "download"])
    ap.add_argument("kind", choices=TASKS)
    args = ap.parse_args()
    manifest = verify()
    slug, source = TASKS[args.kind]
    if args.kind == "sonnet":
        repair = json.loads((HERE / "freeze_sonnet.json").read_text(encoding="utf-8"))
        assert hashlib.sha256((HERE / source).read_bytes()).hexdigest() == repair["task_sha256"]
        assert hashlib.sha256((HERE / "freeze.json").read_bytes()).hexdigest() == repair["parent_freeze_sha256"]
    models = manifest["writer_models"] if args.kind == "writer" else (["claude-sonnet-5-default"] if args.kind == "sonnet" else ["glm-5"])
    api = KaggleApi()
    api.authenticate()
    receipt_dir = HERE / "receipts"
    receipt_dir.mkdir(exist_ok=True)
    fingerprint = hashlib.sha256((HERE / source).read_bytes()).hexdigest()[:12]
    receipt = receipt_dir / (f"{args.kind}_push_{fingerprint}.json" if args.action == "push" else f"{args.kind}_{args.action}.json")
    if args.action == "push":
        if receipt.exists():
            raise RuntimeError("Push was already attempted; inspect status instead of creating another version")
        receipt.write_text(json.dumps({"attempted_at": datetime.now(timezone.utc).isoformat(), "file_sha256": hashlib.sha256((HERE / source).read_bytes()).hexdigest()}), encoding="utf-8")
        api.benchmarks_tasks_push_cli(slug, str(HERE / source))
    elif args.action == "launch":
        if receipt.exists():
            raise RuntimeError("Launch was already attempted; never submit duplicate runs")
        with api.build_kaggle_client() as client:
            q = client.benchmarks.benchmark_tasks_api_client.get_benchmark_task_quota()
            remaining = q.total_daily_quota_allowed - q.daily_quota_used
            existing = api._fetch_task_runs(client, slug, models)
            if existing:
                raise RuntimeError("Remote runs already exist; inspect them instead of resubmitting")
            if remaining < (3.5 if args.kind == "writer" else 1.0 if args.kind == "sonnet" else .5):
                raise RuntimeError(f"Insufficient free quota for planned launch: ${remaining:.4f}")
        receipt.write_text(json.dumps({"attempted_at": datetime.now(timezone.utc).isoformat(), "models": models,
                                       "remaining_before_usd": remaining}, indent=2), encoding="utf-8")
        api.benchmarks_tasks_run_cli(slug, model=models)
    elif args.action == "status":
        with api.build_kaggle_client() as client:
            info = api._get_benchmark_task(slug, client)
            runs = api._fetch_task_runs(client, slug)
            quota = client.benchmarks.benchmark_tasks_api_client.get_benchmark_task_quota()
            snapshot = {"checked_at": datetime.now(timezone.utc).isoformat(), "task": slug,
                        "version": info.slug.version_number, "creation_state": api._clean_enum_str(info.creation_state),
                        "creation_error": info.creation_error_message, "public": info.is_public,
                        "quota_remaining_usd": quota.total_daily_quota_allowed - quota.daily_quota_used,
                        "runs": [{"id": r.id, "model": r.model_version_slug,
                                  "state": api._clean_enum_str(r.state), "started": str(r.start_time),
                                  "ended": str(getattr(r, "end_time", None))} for r in runs]}
        (receipt_dir / f"{args.kind}_status.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        print(json.dumps(snapshot, indent=2))
    elif args.action == "progress":
        import contextlib
        import io
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            api.benchmarks_tasks_log_cli(slug, model=[models[0]])
        lines = buffer.getvalue().splitlines()
        useful = [s for s in lines if any(word in s.lower() for word in ["error", "traceback", "progress", "completed", "evaluat", "running", "not available", "retriev", "log"]) ]
        print("\n".join(s[:350] for s in useful[-15:]))
    else:
        output_kind = "writer" if args.kind == "sonnet" else args.kind
        api.benchmarks_tasks_download_cli(slug, model=models, output=str(HERE / "downloads" / output_kind))


if __name__ == "__main__":
    main()
