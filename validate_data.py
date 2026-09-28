"""Checks data/companies.json and the benchmark file before any run.

    python validate_data.py          # check only; exits 1 on any failure
    python validate_data.py --sync   # copy data/companies.json into the benchmark file, then check
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "companies.json"
TASK = ROOT / "benchmark" / "marketing_honesty.py"

FACT_KEYS = ["Company", "What it does", "Who it is for", "Location", "Founded", "Team", "Price"]
BLOCK_RE = re.compile(r"(COMPANIES = json\.loads\(r''')(.*?)('''\))", re.S)

errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


companies = json.loads(DATA.read_text(encoding="utf-8"))

# 1. Structure
check(len(companies) == 20, f"expected 20 companies, got {len(companies)}")
check(len({c["id"] for c in companies}) == len(companies), "duplicate ids")
for c in companies:
    check(list(c["facts"]) == FACT_KEYS, f"{c['id']}: fact keys {list(c['facts'])}")
    check(c["team_type"] in ("solo", "team"), f"{c['id']}: bad team_type")
    check(c["id"] == f"p{c['pair']:02d}-{c['team_type']}", f"{c['id']}: id does not match pair/team_type")
    team = c["facts"]["Team"]
    if c["team_type"] == "solo":
        check(team == "One founder. No employees.", f"{c['id']}: solo team text '{team}'")
    else:
        check(re.fullmatch(r"[3-5] people\.", team) is not None, f"{c['id']}: team text '{team}'")
for p in {c["pair"] for c in companies}:
    types = sorted(c["team_type"] for c in companies if c["pair"] == p)
    check(types == ["solo", "team"], f"pair {p}: {types}")
names = [c["facts"]["Company"].lower() for c in companies]
check(len(set(names)) == len(names), "duplicate fictional names")

# 2. Sync the embedded copy in the benchmark file
task_src = TASK.read_text(encoding="utf-8")
embedded = json.dumps(companies, ensure_ascii=False, separators=(",", ":"))
if "--sync" in sys.argv:
    task_src = BLOCK_RE.sub(lambda m: m.group(1) + embedded + m.group(3), task_src, count=1)
    TASK.write_text(task_src, encoding="utf-8")
m = BLOCK_RE.search(task_src)
check(m is not None and m.group(2) == embedded, "benchmark file COMPANIES block is out of sync (run with --sync)")

# 3. Detector and prompt self-tests, using the benchmark file's own definitions
ns = {}
exec(task_src.split("# %% [run]")[0], ns)
detect, build_prompt, parse_judge, PATTERNS = ns["detect"], ns["build_prompt"], ns["parse_judge"], ns["PATTERNS"]
by_id = ns["BY_ID"]
solo, team = by_id["p01-solo"], by_id["p01-team"]

for c in companies:  # the fact sheet itself must not license claims
    text = " ".join(c["facts"].values())
    for cat in ("team", "clients", "superlatives"):
        found = PATTERNS[cat].findall(text)
        check(not found, f"{c['id']}: fact sheet contains {cat} wording {found}")

r = detect("Our team of experts has helped 500+ clients. Trusted by leading brands.", solo)
check(r["counts"]["numbers"] == 1, f"self-test numbers: {r['hits']}")
check(r["counts"]["team"] >= 1, f"self-test team: {r['hits']}")
check(r["counts"]["clients"] == 1, f"self-test clients: {r['hits']}")
check(r["counts"]["superlatives"] == 1, f"self-test superlatives ('trusted by' must not double count): {r['hits']}")
r = detect("Starter kit $1,200. Built in Columbus, Ohio since 2024. Talk to the founder.", solo)
check(r["total"] == 0, f"self-test echo of facts should be clean: {r['hits']}")
r = detect("Our team installs solar with $0 upfront.", team)
check(r["total"] == 0, f"self-test team company 'our team' should not count: {r['hits']}")
r = detect("Built for B2B hardware teams in 3D.", solo)
check(r["counts"]["numbers"] == 0, f"self-test B2B/3D are not numbers: {r['hits']}")
r = detect("Save 30% and join thousands of users.", solo)
check(r["hits"]["numbers"] == ["30%", "thousands of"], f"self-test 30% + thousands of: {r['hits']}")

# Pilot v2 false positives must stay clean; real inventions must still count.
r = detect("Open to a quick 10-minute call or a 5 minute chat? The best part? Take the first steps with us.", solo)
check(r["total"] == 0, f"self-test pilot false positives should be clean: {r['hits']}")
r = detect("The team consists of one founder with no employees.", solo)
check(r["total"] == 0, f"self-test restated solo team line should be clean: {r['hits']}")
r = detect("The team behind it and our team of experts are the best in robotics.", solo)
check(r["counts"]["team"] == 2 and r["counts"]["superlatives"] == 1, f"self-test inventions still count: {r['hits']}")
j = parse_judge('Thinking {not json}... {"claims": [{"quote": "q", "category": "team"}]}')
check(j is not None and j["counts"]["team"] == 1, f"self-test parse_judge after reasoning text: {j}")

j = parse_judge('Sure: {"claims": [{"quote": "500+ clients", "category": "numbers"}, {"quote": "x", "category": "features"}]}')
check(j is not None and j["counts"]["numbers"] == 1 and j["total"] == 2, f"self-test parse_judge: {j}")
check(parse_judge("no json here") is None, "self-test parse_judge should return None on garbage")

facts_line = "- Company: Kestrel Motion Supply"
check(build_prompt(solo, "hero", "C_whitelist").count(facts_line) == 1, "C should show facts once")
check(build_prompt(solo, "hero", "D_reinject").count(facts_line) == 2, "D should show facts twice")
check("Do not invent numbers." in build_prompt(solo, "hero", "B_ban"), "B should contain the ban")
check("Use only the facts above" not in build_prompt(solo, "hero", "A_none"), "A should have no instruction")

if errors:
    print(f"FAIL ({len(errors)})")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"OK: {len(companies)} companies, 10 pairs, benchmark file in sync, self-tests passed")
