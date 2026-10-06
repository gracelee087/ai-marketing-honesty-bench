"""Validate frozen inputs, independent raw-record counts, quotes and portable reproduction."""
import collections
import hashlib
import json
import re

import numpy as np
import pandas as pd

import analyze
import extra
from reproduce import verify_bundle


def main():
    manifest = verify_bundle()
    article = (analyze.ROOT / "post" / "draft.md").read_text(encoding="utf-8")
    evidence = json.loads((analyze.ROOT / "results" / "analysis" / "article_evidence.json").read_text(encoding="utf-8"))
    companies = {c["id"]: c for c in json.loads((analyze.ROOT / "data" / "companies.json").read_text(encoding="utf-8"))}
    totals = collections.Counter()
    conditions = collections.defaultdict(collections.Counter)
    texts = []
    quote_sources = []
    founder_source = None
    for entry in manifest["files"]:
        rows = [json.loads(s) for s in (analyze.ROOT / entry["file"]).read_text(encoding="utf-8").splitlines()]
        keys = [(r["company_id"], r["copy_type"], r["condition"], r["repeat"]) for r in rows]
        assert len(keys) == len(set(keys)) == 288, entry["model"]
        expected = {(c, t, p, k) for c in companies for t in ("hero", "linkedin", "cold_email")
                    for p in analyze.CONDITIONS for k in (range(3) if companies[c]["pair"] == 1 else range(1))}
        assert set(keys) == expected, entry["model"]
        for r in rows:
            if "not_measured" in r:
                assert not r.get("copy") and not r.get("reader")
                continue
            c = companies[r["company_id"]]
            assert (r["pair"], r["team_type"]) == (c["pair"], c["team_type"])
            assert r.get("copy"), (entry["model"], keys)
            totals["generated"] += 1
            texts.append(r["copy"])
            for scorer in ("reader", "detector"):
                score = r.get(scorer)
                if score:
                    assert score["total"] == sum(score["counts"].values())
            rd = r.get("reader")
            if rd:
                totals["read"] += 1
                assert rd["total"] == len(rd["claims"])
                category_counts = collections.Counter(x["category"] for x in rd["claims"])
                assert set(category_counts) <= set(analyze.READER_CATS)
                assert all(rd["counts"][k] == category_counts[k] for k in analyze.READER_CATS)
                if r["repeat"] == 0:
                    q = conditions[r["condition"]]
                    q["read"] += 1
                    q["clean"] += rd["total"] == 0
                    q["claims"] += rd["total"]
            if r["repeat"] == 0 and r["team_type"] == "solo":
                q = conditions[r["condition"]]
                q["solo_generated"] += 1
                q["says_no_employees"] += bool(re.search(r"no employees|zero employees|no[- ‑]employee|without employees|0 employees", r["copy"], re.I))
            if entry["model"] == "gemini-3.8-flash" and r["company_id"] == "p04-solo" and r["copy_type"] == "cold_email" and r["repeat"] == 0 and r["condition"] in ("A_none", "C_whitelist"):
                quote_sources.append(r)
            if entry["model"] == "claude-sonnet-4-5" and r["company_id"] == "p07-solo" and r["copy_type"] == "linkedin" and r["condition"] == "C_whitelist" and r["repeat"] == 0:
                assert founder_source is None
                founder_source = r
                source_link = f"https://github.com/gracelee087/ai-marketing-honesty-bench/blob/master/{entry['file']}#L{rows.index(r) + 1}"
                assert source_link in article
        assert sum(bool(r.get("reader")) for r in rows) == entry["read"]
        assert sum(bool(r.get("copy")) for r in rows) == entry["generated"]
    assert totals == {"generated": 2898, "read": 2665}
    assert sum(v["read"] for v in conditions.values()) == evidence["read_first"] == 2208
    for row in evidence["prompt"]:
        raw = conditions[row["condition"]]
        assert row["read"] == raw["read"] and row["reader_clean"] == raw["clean"]
        assert row["says_no_employees"] == raw["says_no_employees"]
        assert row["solo_generated"] == raw["solo_generated"]
        assert np.isclose(row["claims_mean"], raw["claims"] / raw["read"])
        assert f"{raw['clean']} / {raw['read']} ({raw['clean'] / raw['read']:.1%})" in article
        assert f"{raw['says_no_employees']} / {raw['solo_generated']} ({raw['says_no_employees'] / raw['solo_generated']:.1%})" in article
    rank = pd.read_csv(analyze.ROOT / "results" / "analysis" / "headline_ranking_core.csv")
    for r in rank.itertuples():
        assert f"| {r.model} | {r.reader_clean:.1%} | {r.n} |" in article
    quotes = re.findall(r"^> (.+)$", article, re.M)
    assert founder_source is not None
    for quote in quotes:
        assert any(quote in r["copy"] for r in [*quote_sources, founder_source]), f"Quote not in illustrative source: {quote}"
    assert len(quote_sources) == 2
    assert sorted(r["reader"]["total"] for r in quote_sources) == [0, 2]
    founder_quote = "After years of working in fixed income markets, I saw how fragmented the research process had become."
    assert founder_quote in quotes and founder_quote in founder_source["copy"]
    career_claim = "After years of working in fixed income markets"
    assert any(c["quote"] == career_claim for c in founder_source["reader"]["claims"])
    for fragment in (career_claim, "I saw how fragmented the research process had become."):
        assert fragment in article and fragment in founder_source["copy"]
    for company_id in ("p07-solo", "p04-solo"):
        brief = "\n".join(f"{k}: {v}" for k, v in companies[company_id]["facts"].items())
        assert f"```text\n{brief}\n```" in article
    print("Founder example PASS: exact Sonnet 4.5 facts-only LinkedIn quote; career claim flagged; complete quoted briefs and source line link.")
    assert not re.search(r"KAGGLE_BENCHMARK_URL|TODO|TBD|\[INSERT", article)
    for path in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", article):
        assert (analyze.ROOT / "post" / path).is_file(), path
    original = analyze.RUNS
    analyze.RUNS = analyze.ROOT / "results" / "selected_runs"
    portable, portable_missing, _ = analyze.load()
    portable_extra, _ = extra.load()
    gem = portable_extra[(portable_extra.model == "gemini-3.8-flash") & (portable_extra.condition == "C_whitelist")]
    assert len(gem) == 60 and gem.read.all() and (gem.claims == 0).all()
    case = evidence["gemini_case"]
    for copy_type, flag in (("linkedin", "excited"), ("cold_email", "open_to"), (None, "em_dash")):
        for condition in ("A_none", "C_whitelist"):
            population = portable_extra[portable_extra.condition == condition]
            if copy_type is not None:
                population = population[population.copy_type == copy_type]
            count, denominator = int(population[flag].sum()), len(population)
            assert f"{count} / {denominator} ({count / denominator:.1%})" in article, (copy_type, flag, condition)
    actual_case = {"n": len(gem), "reader_clean": int((gem.claims == 0).sum()),
                   "at_least_half_fact_overlap": int((gem.paste >= .5).sum()),
                   "at_least_5pct_repeated_4grams": int((gem.repeat_pct >= 5).sum()),
                   "says_no_employees": int(gem.no_employees.sum()),
                   "passes_three": int(extra.passes_checks(gem, ask=False).sum())}
    assert all(case[k] == v for k, v in actual_case.items())
    assert all(f"{v} / 60" in article for v in (29, 23, 19, 12))
    cached = pd.read_csv(analyze.ROOT / "results" / "analysis" / "items.csv")
    pd.testing.assert_frame_equal(portable.drop(columns="claims"), cached, check_dtype=False, atol=1e-12)
    if original.exists():
        analyze.RUNS = original
        original_df, original_missing, _ = analyze.load()
        original_extra, _ = extra.load()
        pd.testing.assert_frame_equal(portable, original_df)
        pd.testing.assert_frame_equal(portable_extra, original_extra)
        assert portable_missing == original_missing
        print("Original and exported responses produce identical primary and exploratory item tables.")
    followup = analyze.ROOT / "validation_2026-10-05"
    frozen = json.loads((followup / "freeze.json").read_text(encoding="utf-8"))
    for name, digest in frozen["files"].items():
        assert hashlib.sha256((followup / name).read_bytes()).hexdigest() == digest, name
    raw_manifest = json.loads((followup / "out" / "response_manifest.json").read_text(encoding="utf-8"))
    assert len(raw_manifest) == 5
    for entry in raw_manifest:
        assert hashlib.sha256((followup / entry["file"]).read_bytes()).hexdigest() == entry["sha256"]
    followup_summary = json.loads((followup / "out" / "summary.json").read_text(encoding="utf-8"))
    assert followup_summary["generated"] == followup_summary["recorded"] == 120
    assert followup_summary["read"] == 109 and followup_summary["controls_recorded"] == 30
    assert f"**{followup_summary['generated']} emails**" in article
    assert f"scored **{followup_summary['read']}**" in article
    for row in followup_summary["conditions"]:
        assert f"{row['clean_n']}/{row['read']}" in article
        assert f"{row['mean_overlap']:.1%}" in article
        assert f"{row['says_no_employees']}/{row['solo_generated']}" in article
    contrasts = {(r["contrast"], r["measure"]): r for r in followup_summary["contrasts"]}
    for contrast in ("C-A", "E-C"):
        for key in ("difference", "lo", "hi"):
            formatted = f"{100 * contrasts[(contrast, 'overlap')][key]:.2f}".replace("-", "−")
            assert formatted in article, formatted
    assert contrasts[("E-C", "clean")]["difference"] == 0
    assert contrasts[("E-C", "clean")]["n_pairs"] == 35
    assert "35 matched scored pairs was zero" in article
    controls = pd.read_csv(followup / "out" / "controls.csv")
    assert len(controls) == 30 and controls["pass"].all()
    print("Follow-up PASS: 120 generated, 109 scored, 30 controls; frozen sources and saved-response hashes; article counts and paired overlap intervals.")
    print(f"PASS: {len(manifest['files'])} complete 288-key grids; scorer arithmetic; {sum(v['read'] for v in conditions.values())} first-repeat scores; article numerators and six style frequencies; 11 model rows; {len(quotes)} exact quotes; image paths; input hashes.")


if __name__ == "__main__":
    main()
