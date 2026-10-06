"""Offline, frozen analysis of the new-company validation; no human ratings inferred."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine import CONDITIONS, SEED, control_pass, measures

HERE = Path(__file__).resolve().parent
COMPANIES = {c["id"]: c for c in json.loads((HERE / "companies.json").read_text(encoding="utf-8"))}


def verify_freeze():
    manifest = json.loads((HERE / "freeze.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected, f"Frozen input changed: {name}"
    return manifest


def boot(values, companies):
    g = pd.DataFrame({"v": np.asarray(values, float), "c": np.asarray(companies)}).groupby("c").v
    sums, counts = g.sum().to_numpy(), g.count().to_numpy()
    rng = np.random.default_rng(SEED)
    ix = rng.integers(0, len(sums), size=(10000, len(sums)))
    estimates = sums[ix].sum(axis=1) / counts[ix].sum(axis=1)
    return float(sums.sum() / counts.sum()), *map(float, np.percentile(estimates, [2.5, 97.5]))


def table(df):
    text = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    for row in df.itertuples(index=False):
        text += "| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in row) + " |\n"
    return text


def main():
    manifest = verify_freeze()
    rows, provenance = [], []
    for source in sorted((HERE / "downloads" / "writer").rglob("results.jsonl")):
        model = next((m for m in manifest["writer_models"] if m in source.parts), None)
        if model is None:
            raise ValueError(f"Unknown model directory: {source}")
        records = [json.loads(s) for s in source.read_text(encoding="utf-8").splitlines()]
        provenance.append({"model": model, "run_id": source.parent.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "file": str(source.relative_to(HERE))})
        for r in records:
            c = COMPANIES[r["company_id"]]
            item = {"model": model, "company": r["company_id"], "team_type": c["team_type"],
                    "condition": r["condition"], "status": r["status"], "generated": bool(r.get("copy")),
                    "read": r.get("reader") is not None,
                    "clean": float(r["reader"]["total"] == 0) if r.get("reader") is not None else np.nan,
                    "claims": r["reader"]["total"] if r.get("reader") is not None else np.nan,
                    "cost_usd": sum((r.get(k) or {}).get("cost_nanodollars", 0) or 0 for k in ("usage", "reader_usage")) / 1e9,
                    "writer_at_token_cap": r.get("writer_at_token_cap", False),
                    "reader_at_token_cap": r.get("reader_at_token_cap", False)}
            if r.get("copy"):
                recomputed = measures(c, r["copy"])
                for k, v in recomputed.items():
                    assert k not in r or r[k] == v, (model, r["company_id"], k)
                item.update(recomputed)
            rows.append(item)
    if not rows:
        raise RuntimeError("No downloaded validation responses yet")
    d = pd.DataFrame(rows)
    assert not d.duplicated(["model", "company", "condition"]).any(), "Multiple responses for a planned item; do not select a better run"
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    d.to_csv(out / "items.csv", index=False)
    summaries = []
    for condition in CONDITIONS:
        g = d[d.condition == condition]
        generated, read = g[g.generated], g[g.read]
        solo = generated[generated.team_type == "solo"]
        summaries.append({"condition": condition, "planned": 40, "recorded": len(g), "generated": len(generated),
                          "read": len(read), "clean_n": int(read.clean.sum()), "clean_share": read.clean.mean(),
                          "mean_overlap": generated.overlap.mean(), "mean_repeat_share": generated.repeat_share.mean(),
                          "solo_generated": len(solo), "says_no_employees": int(solo.no_employees.sum()),
                          "cost_usd": g.cost_usd.sum()})
    summary = pd.DataFrame(summaries)
    summary.to_csv(out / "conditions.csv", index=False)
    contrasts = []
    for a, b in [("A", "C"), ("C", "E")]:
        for measure in ["clean", "claims", "overlap", "repeat_share", "no_employees"]:
            pop = d[d.team_type == "solo"] if measure == "no_employees" else d
            wide = pop.pivot(index=["model", "company"], columns="condition", values=measure)
            if a not in wide or b not in wide:
                continue
            paired = wide[[a, b]].dropna().reset_index()
            if paired.empty:
                continue
            estimate, low, high = boot(paired[b].astype(float) - paired[a].astype(float), paired.company)
            per_model_n = paired.groupby("model").size()
            sufficient = len(per_model_n) == 4 and per_model_n.min() >= 8 and len(paired) >= 30
            contrasts.append({"contrast": f"{b}-{a}", "measure": measure, "n_pairs": len(paired),
                              "companies": paired.company.nunique(), "difference": estimate, "lo": low, "hi": high,
                              "coverage": "complete-enough" if sufficient else "descriptive"})
    comparison = pd.DataFrame(contrasts)
    comparison.to_csv(out / "contrasts.csv", index=False)
    model_summary = d.groupby(["model", "condition"]).agg(recorded=("status", "size"), generated=("generated", "sum"),
                    read=("read", "sum"), clean_share=("clean", "mean"), mean_overlap=("overlap", "mean"),
                    mean_repeat_share=("repeat_share", "mean"), cost_usd=("cost_usd", "sum")).reset_index()
    model_summary.to_csv(out / "by_model.csv", index=False)
    controls = []
    for source in sorted((HERE / "downloads" / "controls").rglob("results.jsonl")):
        for line in source.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            controls.append({"company": r["company_id"], "kind": r["kind"], "status": r["status"],
                             "pass": control_pass(r["kind"], r.get("reader")),
                             "reader_raw": r.get("reader_raw", ""),
                             "cost_usd": ((r.get("reader_usage") or {}).get("cost_nanodollars") or 0) / 1e9})
    controls_df = pd.DataFrame(controls)
    controls_text = "Controls not yet available.\n"
    if len(controls_df):
        assert not controls_df.duplicated(["company", "kind"]).any()
        controls_df.to_csv(out / "controls.csv", index=False)
        control_summary = controls_df.groupby("kind").agg(recorded=("status", "size"), scored=("pass", "count"), passed=("pass", "sum")).reset_index()
        controls_text = table(control_summary)
    status = d.groupby(["model", "status"]).size().rename("n").reset_index()
    report = ["# New-company follow-up results\n\n", f"Frozen: {manifest['frozen_at_utc']}. No human evaluation.\n\n",
              "Ten fictional company briefs, four selected writers, one email each under A / C / E. E adds only permission to select relevant facts. Text figures use generated copies; reader figures exclude invalid/missing judgments.\n\n",
              "## Conditions\n\n", table(summary), "\n## Paired changes\n\n", table(comparison),
              "\nChanges are B minus A as named in each contrast. Intervals resample ten companies 10,000 times; small-sample and judge uncertainty remain. No interval establishes marketing usability. Staffing has five companies and is secondary.\n\n",
              "## By model\n\n", table(model_summary), "\n## Status and missingness\n\n", table(status),
              f"\nWriter cap reached: {int(d.writer_at_token_cap.sum())}; reader cap reached: {int(d.reader_at_token_cap.sum())}.\n",
              "\n## Synthetic reader controls\n\n", controls_text,
              "\nThese known-construction controls test obvious restatements and injected numeric claims. They are not human calibration or an accuracy estimate on natural marketing prose.\n"]
    (out / "report.md").write_text("".join(report), encoding="utf-8")
    result = {"human_validation": False, "recorded": len(d), "planned": 120, "generated": int(d.generated.sum()),
              "read": int(d.read.sum()), "cost_usd": float(d.cost_usd.sum() + (controls_df.cost_usd.sum() if len(controls_df) else 0)),
              "controls_recorded": len(controls_df), "conditions": summaries, "contrasts": contrasts, "runs": provenance}
    (out / "summary.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["recorded", "generated", "read", "cost_usd", "controls_recorded"]}))
    print(summary.to_string(index=False))
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
