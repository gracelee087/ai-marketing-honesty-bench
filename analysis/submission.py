"""Small, traceable evidence set and exportable charts for the DEV article."""
import json
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import analyze
import extra
from invitations import invitation_evidence, RULE_VERSION

COLORS = ["#46576c", "#5483b4", "#0a8077", "#ae7146"]
LABELS = ["A  No instruction", "B  Number ban", "C  Facts only", "D  Facts repeated"]


def _chart_style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "axes.spines.bottom": False,
                         "figure.facecolor": "#faf9f5", "axes.facecolor": "#faf9f5",
                         "text.color": "#172b38", "axes.labelcolor": "#172b38",
                         "xtick.color": "#46576c", "ytick.color": "#172b38"})


def _bar(path, title, subtitle, values, annotations, xlabel, xmax):
    fig, ax = plt.subplots(figsize=(10, 5.4))
    y = np.arange(4)
    ax.barh(y, values, color=COLORS, height=.55)
    ax.set_yticks(y, LABELS)
    ax.invert_yaxis()
    ax.set_xlim(0, xmax)
    ax.set_xlabel(xlabel, labelpad=10)
    ax.tick_params(length=0)
    ax.xaxis.grid(True, color="#e1e3df", linewidth=.7)
    ax.set_axisbelow(True)
    for i, (value, annotation) in enumerate(zip(values, annotations)):
        ax.text(value + xmax * .015, i, annotation, va="center", fontsize=12, fontweight="bold")
    fig.text(.04, .94, title, fontsize=20, fontweight="bold", ha="left")
    fig.text(.04, .885, subtitle, fontsize=10.5, ha="left", color="#46576c")
    fig.subplots_adjust(left=.24, right=.96, top=.80, bottom=.18)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build(out):
    df, missing, notes = analyze.load()
    d, _ = extra.load()
    f = analyze.first(df)
    rows = []
    for condition in analyze.CONDITIONS:
        r = f[f.condition == condition]
        g = d[d.condition == condition]
        solo = g[g.team_type == "solo"]
        long_ = g[g.copy_type != "hero"]
        rows.append({"condition": condition, "read": len(r), "reader_clean": int((r.rd_total == 0).sum()),
                     "clean_share": float((r.rd_total == 0).mean()), "claims_mean": float(r.rd_total.mean()),
                     "generated": len(g), "mean_fact_overlap": float(g.paste.mean()),
                     "solo_generated": len(solo), "says_no_employees": int(solo.no_employees.sum()),
                     "longform_mean_repeated_4grams_pct": float(long_.repeat_pct.mean())})
    prompt = pd.DataFrame(rows)
    prompt.to_csv(out / "article_prompt_evidence.csv", index=False)
    clean = d[d.read].assign(clean=lambda x: (x.claims == 0).astype(float))
    # Explicitly omit the invitation heuristic from these three visible text checks.
    clean["passes_three"] = extra.passes_checks(clean, ask=False)
    clean["clean_and_three"] = clean.clean * clean.passes_three
    gem = clean[(clean.model == "gemini-3.8-flash") & (clean.condition == "C_whitelist")]
    case = {"model": "gemini-3.8-flash", "condition": "C_whitelist", "n": len(gem),
            "reader_clean": int(gem.clean.sum()), "at_least_half_fact_overlap": int((gem.paste >= .5).sum()),
            "at_least_5pct_repeated_4grams": int((gem.repeat_pct >= 5).sum()),
            "says_no_employees": int(gem.no_employees.sum()), "passes_three": int(gem.passes_three.sum())}
    core = clean[clean.pair <= analyze.CORE_PAIRS]
    names = core.groupby("model").size().loc[lambda x: x >= 100].index
    common = core[core.model.isin(names)].pivot(index=["company", "copy_type", "condition"], columns="model", values="clean").dropna()
    common.mean().rename("reader_clean").to_csv(out / "article_common_items.csv")
    raw = []
    coverage = []
    invitations = []
    for model, run, _ in analyze.chosen_runs():
        records = [json.loads(s) for s in (run / "results.jsonl").read_text(encoding="utf-8").splitlines()]
        coverage.append({"model": model, "run": run.name, "planned": 288,
                         "generated": sum(bool(r.get("copy")) for r in records),
                         "read_all_repeats": sum(bool(r.get("reader")) for r in records),
                         "read_first": sum(bool(r.get("reader")) and r["repeat"] == 0 for r in records)})
        for r in records:
            if r.get("copy_type") == "cold_email" and r.get("repeat") == 0 and r.get("copy"):
                invitations.append({"model": model, "company": r["company_id"], "condition": r["condition"],
                                    **invitation_evidence(r["copy"]), "copy": r["copy"]})
            if model == "gemini-3.8-flash" and r.get("company_id") == "p04-solo" and r.get("copy_type") == "cold_email" and r.get("repeat") == 0 and r.get("condition") in ("A_none", "C_whitelist"):
                raw.append({"model": model, "run": run.name, **r})
    pd.DataFrame(coverage).to_csv(out / "article_coverage.csv", index=False)
    pd.DataFrame(invitations).to_csv(out / "invitation_cues_audit.csv", index=False)
    evidence = {"generated_all_repeats": int(sum(c["generated"] for c in coverage)),
                "read_all_repeats": int(sum(c["read_all_repeats"] for c in coverage)),
                "read_first": len(f), "prompt": rows, "gemini_case": case,
                "common_items": len(common), "common_models": len(names),
                "invitation_rule": RULE_VERSION, "illustrative_pair": raw,
                "scope": "Prompt summaries use all available first-repeat items; cross-model tables use pairs 1–6. Text-only measures include generated items even if the reader failed."}
    (out / "article_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _chart_style()
    assets = out / "article_assets"
    assets.mkdir(exist_ok=True)
    _bar(assets / "01_reader_clean.png", "The factuality instruction improved the checker score",
         "First-repeat texts · all 20 companies · available reader-scored items · one AI checker, no human grading",
         100 * prompt.clean_share, [f"{x.clean_share:.1%}  ({x.reader_clean}/{x.read})" for x in prompt.itertuples()],
         "Texts with zero unsupported claims identified by glm-5 (%)", 105)
    _bar(assets / "02_no_employees.png", 'The copy also started saying “no employees”',
         "Exploratory text match · solo-founder companies · all three formats · generated first-repeat texts",
         100 * prompt.says_no_employees / prompt.solo_generated,
         [f"{x.says_no_employees / x.solo_generated:.1%}  ({x.says_no_employees}/{x.solo_generated})" for x in prompt.itertuples()],
         'Texts containing “no employees” or a listed spelling variant (%)', 31)
    print(f"Article evidence: {len(f)} scored first-repeat texts; Gemini C case {case}; common items {len(common)} × {len(names)} models")


if __name__ == "__main__":
    build(analyze.OUT)
