"""Export the selected saved runs for offline reproduction. Never calls a model."""
import hashlib
import json
from pathlib import Path

import pandas as pd

import analyze

FIELDS = {
    "company_id", "pair", "team_type", "copy_type", "condition", "repeat", "copy",
    "detector", "reader", "reader_model", "usage", "reader_usage", "not_measured",
}
USAGE = {"input_tokens", "output_tokens", "cost_nanodollars", "latency_ms"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = analyze.ROOT / "results" / "selected_runs"
    entries = []
    for model, run, _ in analyze.chosen_runs():
        source = run / "results.jsonl"
        dest = target / source.relative_to(analyze.RUNS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        rows = [json.loads(s) for s in source.read_text(encoding="utf-8").splitlines()]
        public = []
        for row in rows:
            r = {k: v for k, v in row.items() if k in FIELDS}
            # Error messages and provider response envelopes are not needed for reproduction.
            if "not_measured" in r:
                info = row["not_measured"]
                if isinstance(info, dict):
                    r.update({k: info[k] for k in ("company_id", "copy_type", "condition", "repeat") if k in info})
                r["not_measured"] = True
            for key in ("usage", "reader_usage"):
                if r.get(key):
                    r[key] = {k: v for k, v in r[key].items() if k in USAGE}
            public.append(r)
        dest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in public), encoding="utf-8")
        entries.append({"model": model, "run_id": run.name,
                        "file": dest.relative_to(analyze.ROOT).as_posix(), "sha256": sha(dest),
                        "source_sha256": sha(source), "rows": len(rows),
                        "generated": sum(bool(r.get("copy")) for r in rows),
                        "read": sum(bool(r.get("reader")) for r in rows)})
    manifest = {"task_version": analyze.VERSION,
                "selection": "Most reader-scored items including repeats; tie: later run ID. Never merge runs.",
                "transform": "Allowlisted record fields; usage fields allowlisted; error text omitted; not_measured normalized to true.",
                "files": entries,
                "inputs": [{"file": p, "sha256": sha(analyze.ROOT / p)}
                           for p in ["data/companies.json", "benchmark/marketing_honesty.py", "HYPOTHESES.md"]]}
    selected = {(e["model"], e["run_id"]) for e in entries}
    candidates = []
    for tree in (analyze.RUNS, analyze.ROOT / "runs_unused" / "which-ai-lies-less-in-marketing-copy"):
        for source in sorted((tree / analyze.VERSION).glob("*/*/results.jsonl")):
            records = [json.loads(s) for s in source.read_text(encoding="utf-8").splitlines()]
            model, run_id = analyze.display_name(source.parent.parent.name), source.parent.name
            candidates.append({"model": model, "run_id": run_id, "reader_scored": sum(bool(r.get("reader")) for r in records),
                               "generated": sum(bool(r.get("copy")) for r in records), "selected": (model, run_id) in selected})
    audit = pd.DataFrame(candidates).drop_duplicates(["model", "run_id"])
    for model, g in audit.groupby("model"):
        chosen = g.sort_values(["reader_scored", "run_id"]).iloc[-1]
        assert chosen.selected, f"Selected run is not the highest-coverage known run for {model}"
    audit.to_csv(analyze.ROOT / "results" / "run_selection.csv", index=False)
    manifest["run_selection_scope"] = "All version-4 result files available in local runs and runs_unused; earlier attempts without saved files are not reconstructed."
    manifest["inputs"].append({"file": "results/run_selection.csv", "sha256": sha(analyze.ROOT / "results" / "run_selection.csv")})
    (analyze.ROOT / "results" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(entries)} selected runs; generated={sum(e['generated'] for e in entries)}, read={sum(e['read'] for e in entries)}")


if __name__ == "__main__":
    main()
