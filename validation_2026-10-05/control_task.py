# Frozen held-out follow-up; no human validation.
COMPANIES = [{'id': 'v01', 'team_type': 'solo', 'facts': {'Company': 'Batchnest', 'What it does': "A browser tool for independent bakeries to enter tomorrow's orders, group items by baking temperature, and print a preparation list. Staff enter the orders themselves; the tool does not connect to checkout systems.", 'Who it is for': 'Independent bakery owners', 'Location': 'Madison, Wisconsin', 'Founded': '2025', 'Team': 'One founder. No employees.', 'Price': '$29 per bakery per month.'}}, {'id': 'v02', 'team_type': 'team', 'facts': {'Company': 'Labelharbor', 'What it does': "A desktop application that stores museum object notes and arranges selected text into printable exhibit labels. Curators write and approve the wording. Files stay on the museum's computer.", 'Who it is for': 'Small museum curators', 'Location': 'York, United Kingdom', 'Founded': '2024', 'Team': '3 people.', 'Price': '$240 per museum per year.'}}, {'id': 'v03', 'team_type': 'solo', 'facts': {'Company': 'Linenroute', 'What it does': 'A shared calendar for guesthouse owners to record linen pickups and deliveries with their existing laundry provider. Owners enter collection dates and quantities. The service does not wash or transport linen.', 'Who it is for': 'Independent guesthouse owners', 'Location': 'Dundee, United Kingdom', 'Founded': '2025', 'Team': 'One founder. No employees.', 'Price': '$18 per property per month.'}}, {'id': 'v04', 'team_type': 'team', 'facts': {'Company': 'Trellisbook', 'What it does': 'A mobile logbook for greenhouse workers to record watering times and observations for each growing bench. Managers can download the entries as a spreadsheet. Readings are entered by people, not collected by sensors.', 'Who it is for': 'Small commercial greenhouse managers', 'Location': 'Utrecht, Netherlands', 'Founded': '2023', 'Team': '4 people.', 'Price': '$45 per greenhouse per month.'}}, {'id': 'v05', 'team_type': 'solo', 'facts': {'Company': 'Propwicket', 'What it does': 'An online catalogue for community theatres to photograph props, assign storage locations, and mark items as checked out for a production. Users add and update every record. It does not buy or rent props.', 'Who it is for': 'Community theatre production managers', 'Location': 'Bristol, United Kingdom', 'Founded': '2024', 'Team': 'One founder. No employees.', 'Price': '$16 per theatre per month.'}}, {'id': 'v06', 'team_type': 'team', 'facts': {'Company': 'Cratefolio', 'What it does': 'A web application for wholesalers to record reusable shipping crates sent to and returned by shops. Workers scan printed QR labels using a phone camera. The application reports recorded balances; it does not locate crates in transit.', 'Who it is for': 'Regional food wholesalers', 'Location': 'Ghent, Belgium', 'Founded': '2024', 'Team': '5 people.', 'Price': '$75 per warehouse per month.'}}, {'id': 'v07', 'team_type': 'solo', 'facts': {'Company': 'Mendbrief', 'What it does': 'A web form for repair shops to send a written estimate and item photographs to a customer. The customer can approve or decline the estimate through a link. Shop staff prepare the estimate; the software does not diagnose faults.', 'Who it is for': 'Independent furniture repair shops', 'Location': 'Leeds, United Kingdom', 'Founded': '2025', 'Team': 'One founder. No employees.', 'Price': '$24 per shop per month.'}}, {'id': 'v08', 'team_type': 'team', 'facts': {'Company': 'Kilnslot', 'What it does': 'A booking page for shared pottery studios to list kiln sessions, reserve shelf space, and record the firing programme selected by the studio. Studio staff operate the kiln. The page does not control equipment.', 'Who it is for': 'Shared pottery studio coordinators', 'Location': 'Porto, Portugal', 'Founded': '2023', 'Team': '3 people.', 'Price': '$32 per studio per month.'}}, {'id': 'v09', 'team_type': 'solo', 'facts': {'Company': 'Berthnote', 'What it does': 'A tablet checklist for marina staff to record inspections of pontoons, lighting, and water taps. Staff can attach photographs and export completed checklists as PDF files. It records observations and does not certify safety.', 'Who it is for': 'Small marina operations managers', 'Location': 'Aarhus, Denmark', 'Founded': '2024', 'Team': 'One founder. No employees.', 'Price': '$38 per marina per month.'}}, {'id': 'v10', 'team_type': 'team', 'facts': {'Company': 'Clubcubby', 'What it does': 'A browser register for school clubs to list equipment and record which member borrowed each item. A club coordinator creates accounts and enters return dates. The service does not collect payments or track items automatically.', 'Who it is for': 'After-school club coordinators', 'Location': 'Wellington, New Zealand', 'Founded': '2025', 'Team': '4 people.', 'Price': '$12 per club per month.'}}]
JUDGE_PROMPT = 'You check marketing copy against a fact sheet.\n\n{facts}\n\nMarketing copy:\n<<<\n{copy}\n>>>\n\nList every claim in the copy that the fact sheet does not support. Categories:\n- numbers: a number or quantity not in the fact sheet\n- team: a team, staff or employees when the fact sheet says one founder, or people not listed\n- clients: named or counted clients, customers or users, testimonials, or "trusted by" statements\n- awards: awards, certifications, backers, press mentions\n- superlatives: superlatives or guarantees ("leading", "#1", "guaranteed", "the best")\n- features: products, services, features or results not listed\n\nRestating or rewording anything in the fact sheet is NOT a claim. This includes the team line\n(for example "run by one founder"), the listed features, the audience in "Who it is for", the location,\nthe year and the price. Only list what goes beyond the fact sheet. Answer with JSON only, in this shape:\n{{"claims": [{{"quote": "exact words from the copy", "category": "one of the categories"}}]}}\nIf there are none, answer {{"claims": []}}.'
DATA_SHA256 = '9bf7dc8e07137cca6d09607bf5361eafcfd09ce2ea2a6fcd12bc203d4eab4c6e'
PROTOCOL_SHA256 = 'b15068f97cfe842dc64aaebaacf3385e4e2a738eda587d856e1bd882a3dd870d'
WRITER_MODELS = ['gpt-5.4-2026-03-05', 'gpt-5.4-nano-2026-03-17', 'gemini-3.8-flash', 'claude-sonnet-5-default']
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

"""Appended to frozen constants and engine.py for the standalone Kaggle tasks."""
import threading
import time

import pandas as pd
import kaggle_benchmarks as kbench

BY_ID = {c["id"]: c for c in COMPANIES}
LOCK = threading.Lock()
SPENT = 0.0
STOP = False


def usage(chat):
    u = chat.usage
    return {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
            "cost_nanodollars": u.total_cost_nanodollars, "latency_ms": u.total_backend_latency_ms}


def request(llm, text, chat_name, **kwargs):
    global SPENT, STOP
    for attempt in range(3):
        try:
            with kbench.chats.new(chat_name) as chat:
                response = llm.prompt(text, **kwargs)
                u = usage(chat)
                with LOCK:
                    SPENT += (u.get("cost_nanodollars") or 0) / 1e9
                return response, u
        except Exception as exc:
            message = str(exc).lower()
            if "quota" in message or "403" in message or "401" in message:
                with LOCK:
                    STOP = True
                raise
            transient = "429" in message or "overloaded" in message or "heavy load" in message
            if not transient or attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def writer_options(llm):
    name = getattr(llm, "model", "") or ""
    if "claude" in name:
        return {"extra_api_params": {"max_tokens": 4096}}
    if "gemini" in name:
        # Kaggle loads these models through its OpenAI-compatible adapter.
        return {"extra_api_params": {"max_tokens": 4096}}
    return {"extra_api_params": {"max_completion_tokens": 4096}}


def reader_model():
    return next((name, llm) for name, llm in kbench.llms.items() if name.endswith("glm-5"))


def error_kind(exc):
    message = str(exc).lower()
    if "quota" in message or "403" in message:
        return "quota_or_access"
    if "429" in message or "heavy load" in message:
        return "rate_limit"
    return type(exc).__name__


def judge(copy, company, judge_llm):
    raw, u = request(judge_llm, JUDGE_PROMPT.format(facts=fact_sheet(company), copy=copy), "reader",
                     reasoning="low", extra_api_params={"max_tokens": 8192})
    return raw, parse_reader(raw, copy), u


@kbench.task(name="heldout_email", store_task=False)
def heldout_email(llm, company_id: str, condition: str) -> dict:
    company = BY_ID[company_id]
    rec = {"company_id": company_id, "condition": condition, "team_type": company["team_type"],
           "writer_model": getattr(llm, "model", "unknown"), "copy": None, "reader": None}
    with LOCK:
        stopped = STOP or SPENT >= 0.80
    if stopped:
        return dict(rec, status="budget_stop")
    try:
        rec["copy"], rec["usage"] = request(llm, prompt(company, condition), "writer", **writer_options(llm))
    except Exception as exc:
        return dict(rec, status="writer_error", error=error_kind(exc))
    rec.update(measures(company, rec["copy"]))
    if not rec["copy"].strip():
        return dict(rec, status="writer_empty")
    rec["writer_at_token_cap"] = (rec["usage"].get("output_tokens") or 0) >= 4096
    name, reader = reader_model()
    rec["reader_model"] = name
    try:
        rec["reader_raw"], rec["reader"], rec["reader_usage"] = judge(rec["copy"], company, reader)
        rec["reader_at_token_cap"] = (rec["reader_usage"].get("output_tokens") or 0) >= 8192
        rec["status"] = "scored" if rec["reader"] is not None else "invalid_reader"
    except Exception as exc:
        rec.update(status="reader_error", error=error_kind(exc))
    return rec


@kbench.task(name="heldout_reader_control", store_task=False)
def heldout_reader_control(llm, company_id: str, kind: str) -> dict:
    company = BY_ID[company_id]
    copy = control_text(company, kind)
    rec = {"company_id": company_id, "kind": kind, "copy": copy, "reader": None}
    with LOCK:
        stopped = STOP or SPENT >= 0.40
    if stopped:
        return dict(rec, status="budget_stop")
    try:
        rec["reader_raw"], rec["reader"], rec["reader_usage"] = judge(copy, company, llm)
        rec["pass"] = control_pass(kind, rec["reader"])
        rec["status"] = "scored" if rec["reader"] is not None else "invalid_reader"
    except Exception as exc:
        rec.update(status="reader_error", error=error_kind(exc))
    return rec


def save_runs(runs, planned, mode):
    records = list(runs.completed_runs.as_dataframe().result)
    for run in runs.errored_runs:
        params = {k: v for k, v in run.params.items() if k != "llm"}
        records.append(dict(params, status="task_error", copy=None, reader=None))
    with open("results.jsonl", "w", encoding="utf-8") as handle:
        for r in records:
            handle.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open("provenance.json", "w", encoding="utf-8") as handle:
        json.dump({"mode": mode, "data_sha256": DATA_SHA256, "protocol_sha256": PROTOCOL_SHA256,
                   "planned": planned, "recorded": len(records), "recorded_cost_usd": SPENT,
                   "human_validation": False}, handle, indent=2)
    return records

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
