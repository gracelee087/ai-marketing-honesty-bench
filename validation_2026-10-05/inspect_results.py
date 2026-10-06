"""Check raw responses and print contrasting C/E examples after the locked analysis."""
import hashlib
import json
import sys
from pathlib import Path

from analyze import verify_freeze
from engine import CONDITIONS, control_pass, control_text, measures, parse_reader

HERE = Path(__file__).resolve().parent


def main():
    manifest = verify_freeze()
    repair = json.loads((HERE / "freeze_sonnet.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "freeze.json").read_bytes()).hexdigest() == repair["parent_freeze_sha256"]
    assert hashlib.sha256((HERE / repair["task_file"]).read_bytes()).hexdigest() == repair["task_sha256"]
    companies = {c["id"]: c for c in json.loads((HERE / "companies.json").read_text(encoding="utf-8"))}
    all_rows = []
    raw_manifest = []
    for source in sorted((HERE / "downloads" / "writer").rglob("results.jsonl")):
        model = next(m for m in manifest["writer_models"] if m in source.parts)
        rows = [json.loads(s) for s in source.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 30
        provenance = json.loads(source.with_name("provenance.json").read_text(encoding="utf-8"))
        assert provenance["data_sha256"] == manifest["files"]["companies.json"]
        assert provenance["protocol_sha256"] == manifest["files"]["PROTOCOL.md"]
        assert provenance["recorded"] == provenance["planned"] == 30
        assert provenance["human_validation"] is False
        raw_manifest.append({"file": source.relative_to(HERE).as_posix(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        assert {(r["company_id"], r["condition"]) for r in rows} == {(c, p) for c in companies for p in CONDITIONS}
        for row in rows:
            if row.get("copy"):
                assert all(row[k] == v for k, v in measures(companies[row["company_id"]], row["copy"]).items())
            if "reader_raw" in row:
                assert row.get("reader") == parse_reader(row["reader_raw"], row["copy"])
            all_rows.append(dict(row, model=model, run_id=source.parent.name))
    assert len(all_rows) == 120, "Final verification requires all four planned runs."
    assert {r["model"] for r in all_rows} == set(manifest["writer_models"])
    assert len({(r["model"], r["company_id"], r["condition"]) for r in all_rows}) == 120
    controls = []
    for source in sorted((HERE / "downloads" / "controls").rglob("results.jsonl")):
        raw_manifest.append({"file": source.relative_to(HERE).as_posix(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        for line in source.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            assert row["copy"] == control_text(companies[row["company_id"]], row["kind"])
            if "reader_raw" in row:
                assert row.get("reader") == parse_reader(row["reader_raw"], row["copy"])
                assert row.get("pass") == control_pass(row["kind"], row.get("reader"))
            controls.append(row)
    assert len(controls) == 30
    assert {(r["company_id"], r["kind"]) for r in controls} == {(c, k) for c in companies for k in ("supported", "wrong_price", "wrong_team")}
    pairs = []
    index = {(r["model"], r["company_id"], r["condition"]): r for r in all_rows}
    for model in manifest["writer_models"]:
        for company in companies:
            a, b = index.get((model, company, "C")), index.get((model, company, "E"))
            if not a or not b or not a.get("copy") or not b.get("copy"):
                continue
            pairs.append({"model": model, "company": company,
                          "overlap_change": b["overlap"] - a["overlap"], "C": a, "E": b})
    pairs.sort(key=lambda x: x["overlap_change"])
    (HERE / "out" / "paired_examples.json").write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "out" / "response_manifest.json").write_text(json.dumps(raw_manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {len(all_rows)} writer items, {len(controls)} controls, provenance and strict reader parsing; {len(pairs)} C/E pairs exported.")
    selected = [*pairs[:2], *pairs[-1:]]
    for pair in selected:
        print(json.dumps({"model": pair["model"], "company": pair["company"], "overlap_change": pair["overlap_change"],
                          "C": {k: pair["C"].get(k) for k in ["copy", "reader", "overlap", "no_employees"]},
                          "E": {k: pair["E"].get(k) for k in ["copy", "reader", "overlap", "no_employees"]}}, ensure_ascii=False))


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()
