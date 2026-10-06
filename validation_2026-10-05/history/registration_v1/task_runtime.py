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
        return {"extra_api_params": {"max_output_tokens": 4096}}
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
