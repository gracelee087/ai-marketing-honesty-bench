"""Rebuild the analysis from the bundled responses without Kaggle, credentials, or network."""
import argparse
import hashlib
import json
from pathlib import Path

import analyze
import extra
import submission


def verify_bundle():
    manifest = json.loads((analyze.ROOT / "results" / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"] + manifest["inputs"]:
        path = analyze.ROOT / entry["file"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise ValueError(f"Changed input: {entry['file']}")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=analyze.ROOT / "results" / "analysis")
    ap.add_argument("--runs", type=Path, help="Use another saved run tree instead of the verified bundle")
    args = ap.parse_args()
    if args.runs:
        analyze.RUNS = args.runs.resolve()
    else:
        verify_bundle()
        analyze.RUNS = analyze.ROOT / "results" / "selected_runs"
    analyze.OUT = extra.OUT = args.out.resolve()
    analyze.main()
    extra.main()
    submission.build(analyze.OUT)
    print("Offline reproduction complete; no model requests made.")


if __name__ == "__main__":
    main()
