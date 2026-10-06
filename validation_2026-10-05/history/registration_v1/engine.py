"""Frozen pure prompt/scoring functions; task builder injects COMPANIES and JUDGE_PROMPT."""
import json
import random
import re

SEED = 20261005
CONDITIONS = ["A", "C", "E"]
WHITELIST = "Use only the facts above. Do not add numbers, clients, team members, awards, or claims that are not listed."
SELECT = "Select the facts relevant to this audience; you do not need to include every field."
REQUEST = "Write a cold email to a potential customer, with a subject line (100 to 150 words) for {company}. Reply with the copy only."
CATEGORIES = {"numbers", "team", "clients", "awards", "superlatives", "features"}
WORD = re.compile(r"[a-z0-9$%]+(?:'[a-z]+)?")
NO_EMPLOYEES = re.compile(r"no employees|zero employees|no[- ‑]employee|without employees|0 employees", re.I)


def fact_sheet(company):
    return "Fact sheet:\n" + "\n".join(f"- {k}: {v}" for k, v in company["facts"].items())


def prompt(company, condition):
    if condition not in CONDITIONS:
        raise ValueError(condition)
    text = fact_sheet(company) + "\n\n" + REQUEST.format(company=company["facts"]["Company"])
    if condition in ("C", "E"):
        text += "\n" + WHITELIST
    if condition == "E":
        text += "\n" + SELECT
    return text


def schedule(companies):
    rng = random.Random(SEED)
    items = list(companies)
    rng.shuffle(items)
    rows = []
    for company in items:
        order = CONDITIONS.copy()
        rng.shuffle(order)
        rows.extend({"company_id": company["id"], "condition": c} for c in order)
    return rows


def parse_reader(raw, copy):
    value = None
    for match in re.finditer(r'\{\s*"claims"', raw or ""):
        try:
            value = json.JSONDecoder().raw_decode(raw, match.start())[0]
        except (ValueError, TypeError):
            continue
    if not isinstance(value, dict) or not isinstance(value.get("claims"), list):
        return None
    claims = value["claims"]
    counts = {k: 0 for k in sorted(CATEGORIES)}
    for claim in claims:
        if not isinstance(claim, dict) or claim.get("category") not in counts:
            return None
        quote = claim.get("quote")
        if not isinstance(quote, str) or not quote.strip() or quote not in copy:
            return None
        counts[claim["category"]] += 1
    return {"claims": claims, "counts": counts, "total": len(claims)}


def measures(company, copy):
    cw = WORD.findall(copy.lower())
    fw = WORD.findall(" ".join(str(v) for v in company["facts"].values()).lower())
    fact_windows = {tuple(fw[i:i + 4]) for i in range(len(fw) - 3)}
    covered = set()
    windows = [tuple(cw[i:i + 4]) for i in range(max(0, len(cw) - 3))]
    for i, window in enumerate(windows):
        if window in fact_windows:
            covered.update(range(i, i + 4))
    word_count = len(copy.split())
    return {"overlap": len(covered) / max(1, len(cw)),
            "repeat_share": (len(windows) - len(set(windows))) / max(1, len(windows)),
            "no_employees": bool(NO_EMPLOYEES.search(copy)), "word_count": word_count,
            "in_word_limit": 100 <= word_count <= 150, "empty_or_short": word_count < 20}


def control_text(company, kind):
    facts = company["facts"]
    baseline = f"{facts['Company']}. {facts['What it does']} Price: {facts['Price']}"
    if kind == "supported":
        return baseline
    if kind == "wrong_price":
        return f"{facts['Company']}. {facts['What it does']} The price is $987."
    if kind == "wrong_team":
        return baseline + " Our team has 97 employees."
    raise ValueError(kind)


def control_pass(kind, reader):
    if reader is None:
        return None
    if kind == "supported":
        return reader["total"] == 0
    marker = "987" if kind == "wrong_price" else "97"
    return any(re.search(r"(?<!\d)" + marker + r"(?!\d)", c["quote"]) for c in reader["claims"])
