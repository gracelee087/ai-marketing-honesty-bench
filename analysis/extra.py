"""Exploratory analyses added after the data was seen. NOT pre-registered (see HYPOTHESES.md for what was).

The claim tables (hard claims, concrete, nothing added, both) use the LLM reader's lists. The rest is counted
from the text alone, with no LLM:
  - paste:    how much of a copy is lifted word for word from its fact sheet
  - sameness: how often different companies get the same opening, ask and punctuation
  - ban:      whether the number ban moved numbers into vague quantity words
  - pitch:    what else changes with the facts-only line (says "no employees", asks less, repeats itself)
  - checks:   the share of clean copies counted again, keeping only copies that pass four extra automatic checks

    .venv/Scripts/python analysis/extra.py     # writes analysis/out/extra.md, extra_items.csv and four charts
"""
import collections
import json
import re

import numpy as np
import pandas as pd

from analyze import (CONDITIONS, CORE_PAIRS, INK, INK2, MIN_RANKED, OUT, ROOT, SERIES, SURFACE, _save, _style,
                     boot, chosen_runs, compare, md_table)
from analyze import load as analyze_load
from invitations import classify_invitation

PASTE_RUN = 4          # a word counts as pasted when it sits in a run of this many words copied from the fact sheet
MOSTLY_PASTED = 0.5    # a copy counts as "mostly pasted" when at least this share of its words is pasted
SHARED_RUN = 5         # length of the word sequences counted as shared between companies
MIN_PLOTTED = 30       # copies per model and prompt needed to draw the model in the charts
HARD = ["numbers", "team", "clients", "awards"]  # selected reader categories, not verified fabrications
PROMPT = {"A_none": "no instruction", "B_ban": "number ban", "C_whitelist": "facts only",
          "D_reinject": "facts only + repeated"}

WORD = re.compile(r"[a-z0-9$%]+(?:'[a-z]+)?")
STOP = set("a an the and or but of to in on for with at by from as is are was were be been it its this that these "
           "those you your we our us i my they their them he she his her not no so if then than too very can will "
           "just do does did have has had more most less into over under up down out about after before again also "
           "only own same such both each few other some any all who whom which what when where why how one two "
           "three per".split())
EXCITED = re.compile(r"\b(excited|thrilled|proud|delighted)\b", re.I)
OPEN_TO = re.compile(r"\b(would you be open|are you open|open to a)\b", re.I)
N_MINUTE = re.compile(r"\b\d{1,2}[- ]minute", re.I)
PLACEHOLDER = re.compile(r"\[[^\]]{2,30}\]")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
VAGUE = re.compile(r"\b(dozens|hundreds|thousands|millions|countless|numerous|many|several|multiple|a handful|"
                   r"a fraction|significant(?:ly)?|dramatic(?:ally)?|instant(?:ly)?|in (?:minutes|seconds|hours|days|"
                   r"no time)|overnight|every|all your|any|endless|unlimited|most|majority)\b", re.I)
NUMBER = re.compile(r"\d[\d,.]*")
NO_EMPLOYEES = re.compile(r"no employees|zero employees|no[- ‑]employee|without employees|0 employees", re.I)
ONE_FOUNDER = re.compile(r"no employees|one founder|sole founder|solo founder|single founder|one-person|one person|"
                         r"founder and no|without employees", re.I)
TEAM_SIZE = re.compile(r"\b(\d+|three|four|five)[- ](people|person)|team of (\d+|three|four|five)", re.I)
CLOSING = 0.6          # excerpt only; invitation detection uses the full email body
DIGIT = re.compile(r"\d")
CALL_LENGTH = re.compile(r"^\W*((a|an|quick|brief|short|just)\s+)*\d{1,2}\s*[-‐‑ ]?\s*(minutes?|mins?)"
                         r"(\s+(call|chat|demo|conversation|meeting|intro))?\W*$", re.I)
LIMITS = {"linkedin": (120, 180), "cold_email": (100, 150)}  # the word range the request asks for
REPEAT_RUN = 4         # length of the word sequences counted as repeated inside one copy
CHECK_REPEAT = 5.0     # percent of repeated sequences at which a copy fails the "repeats itself" check


def words(text: str) -> list:
    return WORD.findall(text.lower())


def ask_level(text: str, fact_text: str) -> str:
    """Recognized request/offer cues; 'none' is not proof that no invitation exists.

    fact_text is retained for callers; product nouns alone no longer count as requests.
    """
    return classify_invitation(text)


def fields_used(facts: dict, text: str, cw: list, team_type: str) -> int:
    """How many fact-sheet fields besides the company name show up in the copy (rough word match)."""
    low, seen, n = text.lower(), set(cw), 0
    for k, v in facts.items():
        if k == "Company":
            continue
        if k == "Team":
            n += bool((ONE_FOUNDER if team_type == "solo" else TEAM_SIZE).search(low))
        elif k == "Founded":
            n += str(v) in text
        elif k == "Location":
            n += str(v).split(",")[0].lower() in low
        else:
            key = {w for w in words(str(v)) if w not in STOP and len(w) > 2}
            n += len(key & seen) >= max(2, 0.5 * len(key))
    return n


def load():
    companies = {c["id"]: c for c in json.loads((ROOT / "data" / "companies.json").read_text(encoding="utf-8"))}
    rows, masked = [], []
    for model, run, _ in chosen_runs():
        for line in open(run / "results.jsonl", encoding="utf-8"):
            r = json.loads(line)
            if r.get("repeat") != 0 or not r.get("copy"):
                continue
            text, facts = r["copy"], companies[r["company_id"]]["facts"]
            fact_text = " ".join(str(v) for v in facts.values())
            fw, cw = words(fact_text), words(text)
            runs = {tuple(fw[i:i + PASTE_RUN]) for i in range(len(fw) - PASTE_RUN + 1)}
            pasted = [False] * len(cw)
            for i in range(len(cw) - PASTE_RUN + 1):
                if tuple(cw[i:i + PASTE_RUN]) in runs:
                    pasted[i:i + PASTE_RUN] = [True] * PASTE_RUN
            content = [w for w in cw if w not in STOP and len(w) > 2]
            known = set(fw)
            new = [w for w in content if w not in known and w.rstrip("s") not in known and w + "s" not in known]
            fact_numbers = {n.rstrip(".,") for n in NUMBER.findall(fact_text)}
            reader = r.get("reader")
            counts = reader["counts"] if reader else {}
            usage = r.get("usage") or {}
            made_up = [n.rstrip(".,") for n in NUMBER.findall(text) if n.rstrip(".,") not in fact_numbers]
            seqs = [tuple(cw[i:i + REPEAT_RUN]) for i in range(len(cw) - REPEAT_RUN + 1)]
            lo, hi = LIMITS.get(r["copy_type"], (np.nan, np.nan))
            n_words = len(text.split())
            ask = ask_level(text, fact_text) if r["copy_type"] == "cold_email" else ""
            numbers = [c["quote"] for c in (reader["claims"] if reader else []) if c["category"] == "numbers"]
            figures = [q for q in numbers if DIGIT.search(q) and not CALL_LENGTH.match(q)]
            concrete = bool(figures) or bool(counts.get("clients"))
            rows.append({
                "model": model, "company": r["company_id"], "pair": r["pair"], "copy_type": r["copy_type"],
                "team_type": r["team_type"], "no_employees": bool(NO_EMPLOYEES.search(text)),
                "fields_used": fields_used(facts, text, cw, r["team_type"]),
                "repeat_pct": 100 * (len(seqs) - len(set(seqs))) / max(1, len(seqs)),
                "ask": ask, "asks_talk": ask == "conversation", "invites_only": ask == "invitation",
                "no_invite": ask == "none", "concrete": concrete if reader else np.nan,
                "closing": " / ".join(x.strip() for x in text[int(len(text) * CLOSING):].split("\n") if x.strip())
                if ask == "none" else "",
                "n_numbers": len(numbers), "n_digit": sum(bool(DIGIT.search(q)) for q in numbers),
                "n_figures": len(figures),
                "in_limit": lo <= n_words <= hi, "too_long": n_words > hi,
                "condition": r["condition"], "words": len(cw), "read": bool(reader),
                "out_tokens": usage.get("output_tokens") or np.nan,
                "writer_cost": (usage.get("cost_nanodollars") or np.nan) / 1e9, "made_up_numbers": " ".join(made_up),
                "paste": sum(pasted) / max(1, len(cw)), "new_words": len(new) / max(1, len(content)),
                "claims": reader["total"] if reader else np.nan,
                "hard": sum(counts.get(c, 0) for c in HARD) if reader else np.nan,
                "clients": counts.get("clients", 0) if reader else np.nan,
                "detector": r["detector"]["total"],
                "em_dash": "—" in text, "exclamation": "!" in text, "emoji": bool(EMOJI.search(text)),
                "hashtag": bool(re.search(r"#\w+", text)), "excited": bool(EXCITED.search(text[:260])),
                "open_to": bool(OPEN_TO.search(text)), "n_minute": bool(N_MINUTE.search(text)),
                "placeholder": bool(PLACEHOLDER.search(text)),
                "new_numbers": len(made_up),
                "vague": len(VAGUE.findall(text)),
            })
            name = facts["Company"]
            t = re.sub(re.escape(name), "COMPANY", text, flags=re.I)
            for part in name.split():
                if len(part) > 3:
                    t = re.sub(r"\b" + re.escape(part) + r"\b", "COMPANY", t, flags=re.I)
            masked.append((model, r["company_id"], words(t)))
    return pd.DataFrame(rows), masked


def passes_checks(d, paste_max=MOSTLY_PASTED, repeat_max=CHECK_REPEAT, ask=True, staff=True):
    """Four automatic checks added after the data was seen: not mostly pasted, not repeating itself, does not say
    "no employees", and a cold email has a recognized invitation cue. Not a quality rating."""
    ok = (d.paste < paste_max) & (d.repeat_pct < repeat_max)
    if staff:
        ok &= ~d.no_employees
    if ask:
        ok &= ~d.no_invite
    return ok


def pooled_gain(d, col, a, b):
    """All models: change from prompt a to b on the same model, company and copy type, CI over companies."""
    w = d.pivot_table(index=["model", "company", "copy_type"], columns="condition", values=col, aggfunc="first")
    w = w[[a, b]].dropna().reset_index()
    est, lo, hi, n = boot(w[b] - w[a], w["company"])
    return {"measure": col, "from": PROMPT[a], "to": PROMPT[b], "n_pairs": n, "from_mean": w[a].mean(),
            "to_mean": w[b].mean(), "diff": est, "lo": lo, "hi": hi}


def between(d, m1, m2, col):
    """m1 minus m2 on the same company, copy type and prompt, CI over companies."""
    w = d[d.model.isin([m1, m2])].pivot_table(index=["company", "copy_type", "condition"], columns="model",
                                              values=col, aggfunc="first").dropna().reset_index()
    est, lo, hi, n = boot(w[m1] - w[m2], w["company"])
    return {"comparison": f"{m1} minus {m2}", "measure": col, "n_pairs": n, "diff": est, "lo": lo, "hi": hi}


def spread(ys, gap):
    """Label heights for the values ys, pushed apart so that neighbours are at least gap apart.
    Pushing up from the bottom and down from the top and averaging keeps each label near its value."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    up, down, last = {}, {}, None
    for i in order:
        last = ys[i] if last is None or ys[i] - last >= gap else last + gap
        up[i] = last
    last = None
    for i in reversed(order):
        last = ys[i] if last is None or last - ys[i] >= gap else last - gap
        down[i] = last
    return [(up[i] + down[i]) / 2 for i in range(len(ys))]


def pct_table(d, by, cols):
    """Mean of boolean or share columns as shares, with n."""
    t = d.groupby(by)[cols].mean()
    t.insert(0, "n", d.groupby(by).size())
    return t.reset_index()


def wide(d, col, fn="mean"):
    t = d.pivot_table(index="model", columns="condition", values=col, aggfunc=fn).reindex(columns=CONDITIONS)
    n = d.pivot_table(index="model", columns="condition", values=col, aggfunc="size").reindex(columns=CONDITIONS)
    t.insert(0, "n per prompt (min)", n.min(axis=1).astype(int))
    return t.reset_index()


def shared_sequences(masked):
    seen = collections.defaultdict(set)
    writers = collections.defaultdict(set)
    for model, company, w in masked:
        for i in range(len(w) - SHARED_RUN + 1):
            g = tuple(w[i:i + SHARED_RUN])
            seen[g].add(company); writers[g].add(model)
    top = sorted(((len(c), len(writers[g]), " ".join(g)) for g, c in seen.items() if len(c) >= 15), reverse=True)
    return pd.DataFrame(top[:15], columns=["companies", "models", f"{SHARED_RUN}-word sequence"])


def paired_gain(d, col, a="A_none", b="C_whitelist"):
    """Per model: change from a to b on units present in both, with a company-bootstrap 95% CI."""
    rows = []
    for m, g in d.groupby("model"):
        w = g.pivot_table(index=["company", "copy_type"], columns="condition", values=col, aggfunc="first")
        if a not in w or b not in w:
            continue
        w = w[[a, b]].dropna().reset_index()
        if len(w) < MIN_PLOTTED:
            continue
        est, lo, hi, n = boot(w[b] - w[a], w["company"])
        rows.append({"model": m, "n_pairs": n, a: w[a].mean(), b: w[b].mean(), "diff": est, "lo": lo, "hi": hi})
    return pd.DataFrame(rows).sort_values("diff", ascending=False)


def charts(d, plotted, board):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _style(plt)
    pct = matplotlib.ticker.PercentFormatter(1.0)
    r = d[d.read & d.model.isin(plotted)]
    a, c = r[r.condition == "A_none"], r[r.condition == "C_whitelist"]

    # 7. two ways to fail: made-up concrete claims vs words pasted from the fact sheet, per model, A -> C
    fig, ax = plt.subplots(figsize=(8, 5.6))
    ends = []
    for m in plotted:
        x0, y0 = a[a.model == m].paste.mean(), (a[a.model == m].hard > 0).mean()
        x1, y1 = c[c.model == m].paste.mean(), (c[c.model == m].hard > 0).mean()
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", color=SERIES[0], lw=1.8))
        ax.plot([x0], [y0], "o", color=SURFACE, markeredgecolor=SERIES[0], markersize=6, zorder=3)
        ends.append((y1, x1, m))
    boxes = []  # label boxes already placed, as (x0, x1, y0, y1) in data units
    for y1, x1, m in sorted(ends, key=lambda e: -e[1]):  # right-most first; try the spots nearest the arrow head
        w, h = 0.0072 * len(m), 0.026
        for dy in (0, -0.03, 0.03, -0.06, 0.06, 0.09, 0.12):
            box = (x1 + 0.012, x1 + 0.012 + w, y1 + dy - h / 2, y1 + dy + h / 2)
            if not any(box[0] < b[1] and b[0] < box[1] and box[2] < b[3] and b[2] < box[3] for b in boxes):
                break
        boxes.append(box)
        if dy:
            ax.plot([x1, x1 + 0.011], [y1, y1 + dy], color=INK2, linewidth=0.6, zorder=1)
        ax.annotate(m, (x1, y1), xytext=(x1 + 0.012, y1 + dy), textcoords="data", fontsize=9, color=INK2, va="center",
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=0.8, alpha=0.85))
    ax.set_xlim(0, 0.62); ax.set_ylim(-0.08, 0.65)
    ax.xaxis.set_major_formatter(pct); ax.yaxis.set_major_formatter(pct)
    ax.set_xlabel("words copied from the fact sheet (runs of 4+ words), mean per text")
    ax.set_ylabel("reader flags: numbers, team, clients or awards")
    ax.set_title("Two ways to fail: invent, or paste\nopen dot = no instruction, arrow head = with the facts-only line")
    made = [_save(fig, "7_invent_or_paste.png")]

    # 8. share of copies with nothing added, no instruction -> facts-only line, one line per model
    fig, ax = plt.subplots(figsize=(8, 5.2))
    pool = [(a.claims == 0).mean(), (c.claims == 0).mean()]
    ends = []
    for m in plotted:
        y = [(a[a.model == m].claims == 0).mean(), (c[c.model == m].claims == 0).mean()]
        ax.plot([0, 1], y, color=SERIES[0], linewidth=1.6, marker="o", markersize=5, alpha=0.85, clip_on=False)
        ends.append((y[1], m))
    ax.plot([0, 1], pool, color=INK, linewidth=2.4, linestyle="--", marker="o", markersize=5, clip_on=False)
    ends.append((pool[1], "all plotted models"))
    ends.sort()
    placed = []
    for y, m in ends:  # push labels apart so they do not overlap
        ly = y if not placed or y - placed[-1] >= 0.035 else placed[-1] + 0.035
        placed.append(ly)
        ax.annotate(f"{m}  {y:.0%}", (1, y), xytext=(1.03, ly), textcoords="data", fontsize=9, color=INK2, va="center")
    ax.set_xlim(-0.08, 1.75); ax.set_ylim(0, 1.08); ax.yaxis.set_major_formatter(pct)
    ax.set_xticks([0, 1], ["no instruction", "facts-only line"]); ax.grid(axis="x", visible=False)
    ax.set_ylabel("texts where the checker found nothing added")
    ax.set_title("One line in the prompt, model by model")
    made.append(_save(fig, "8_no_instruction_vs_facts_only.png"))

    # 9. what else the facts-only line changes: one row per model, no instruction -> facts-only line
    p = d[d.model.isin(plotted)]
    solo, mail = p[p.team_type == "solo"], p[p.copy_type == "cold_email"]
    order = solo[solo.condition == "C_whitelist"].groupby("model").no_employees.mean().sort_values().index
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.8), sharey=True)
    for ax, g, col, label in [(axes[0], solo, "no_employees", "texts about a one-founder company\nthat say it has no employees"),
                              (axes[1], mail, "asks_talk", "cold emails that ask for\na call, demo, meeting or talk")]:
        t = g.pivot_table(index="model", columns="condition", values=col).reindex(order)
        for i, m in enumerate(order):
            x0, x1 = t.loc[m, "A_none"], t.loc[m, "C_whitelist"]
            ax.plot([x0, x1], [i, i], color=SERIES[0], linewidth=1.8, zorder=2)
            ax.plot([x0], [i], "o", color=SURFACE, markeredgecolor=SERIES[0], markersize=6, zorder=3)
            ax.plot([x1], [i], "o", color=SERIES[0], markersize=6, zorder=3)
        ax.set_xlim(-0.05, 1.05); ax.xaxis.set_major_formatter(pct); ax.set_xlabel(label)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(order)), order)
    fig.suptitle("What else the facts-only line changed\nopen dot = no instruction, filled dot = with the facts-only line",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    made.append(_save(fig, "9_what_else_changed.png"))

    # 10. the clean share counted again: nothing added -> nothing added and passes the four extra checks
    fig, ax = plt.subplots(figsize=(8, 5.6))
    left, right = list(board.nothing_added), list(board.both)
    for m, y0, y1, l0, l1 in zip(board.model, left, right, spread(left, 0.034), spread(right, 0.034)):
        fell = y0 - y1 > 0.2
        color = SERIES[1] if fell else SERIES[0]
        ax.plot([0, 1], [y0, y1], color=color, linewidth=2.2 if fell else 1.5, marker="o", markersize=5,
                alpha=1 if fell else 0.75, clip_on=False)
        ax.annotate(f"{y0:.0%}", (0, y0), xytext=(-0.04, l0), textcoords="data", fontsize=9, color=INK2,
                    va="center", ha="right")
        ax.annotate(f"{m}  {y1:.0%}", (1, y1), xytext=(1.04, l1), textcoords="data", fontsize=9,
                    color=INK if fell else INK2, va="center")
    ax.set_xlim(-0.25, 1.8); ax.set_ylim(0, 0.9); ax.yaxis.set_major_formatter(pct)
    ax.set_xticks([0, 1], ["nothing added\n(what my leaderboard counts)", "nothing added and\npasses four extra checks"])
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("share of texts, first 12 companies, all four prompts")
    ax.set_title("The same texts, counted again")
    made.append(_save(fig, "10_leaderboard_counted_again.png"))
    return made


def main():
    d, masked = load()
    d.to_csv(OUT / "extra_items.csv", index=False)
    r = d[d.read]
    P = ["paste", "new_words", "mostly_pasted", "any_claim", "hard_claim", "client_claim", "detector_flag",
         "em_dash", "exclamation", "emoji", "hashtag", "excited", "open_to", "n_minute", "placeholder",
         "no_employees", "asks_talk", "invites_only", "no_invite", "in_limit", "too_long", "nothing_added", "checks",
         "both", "concrete",
         "from_mean", "to_mean", "lo", "hi", "diff", *CONDITIONS]
    N = ["claims", "claims_without_features", "new_numbers", "vague", "words", "fields_used", "repeat_pct"]

    d = d.assign(mostly_pasted=d.paste >= MOSTLY_PASTED)
    r = r.assign(any_claim=r.claims > 0, hard_claim=r.hard > 0, client_claim=r.clients > 0, detector_flag=r.detector > 0)
    core_n = r[r.pair <= CORE_PAIRS].groupby("model").size()
    per_prompt = r.groupby(["model", "condition"]).size().unstack().reindex(columns=["A_none", "C_whitelist"]).min(axis=1)
    plotted = [m for m in per_prompt.index if per_prompt[m] >= MIN_PLOTTED and core_n.get(m, 0) >= MIN_RANKED]

    s = ["# Exploratory analyses (not pre-registered)\n",
         "Generated by `analysis/extra.py`. First-repeat copies of the reported run of each model. "
         "Tables marked *text only* use no LLM. Every definition and cut-off here was chosen after seeing the data.\n"]

    s += ["\n## 1. Claims by prompt (reader), all models\n",
          "`hard_claim` = at least one claim in the reader's categories " + ", ".join(HARD)
          + ". `detector_flag` = the rule-based detector flagged the copy.\n\n",
          md_table(pct_table(r, "condition", ["any_claim", "hard_claim", "detector_flag", "claims"]), P, N)]
    s += ["\nHard claims, share of copies, by model and prompt:\n", md_table(wide(r, "hard_claim"), P, N)]
    s += ["\nCopies with at least one reader flag in `clients`, by model, all prompts:\n",
          md_table(pct_table(r, "model", ["client_claim"]).sort_values("client_claim", ascending=False), P, N)]
    gain = paired_gain(r.assign(clean=(r.claims == 0).astype(float)), "clean")
    s += [f"\nShare of copies with nothing added, no instruction vs facts-only line, same company and copy type "
          f"(models with at least {MIN_PLOTTED} pairs; 95% CI from resampling companies):\n", md_table(gain, P, N),
          f"\nModels that improved with an interval above zero: {(gain.lo > 0).sum()} of {len(gain)}\n"]

    s += [f"\n## 2. Paste (*text only*)\n`paste` = share of a copy's words inside a run of {PASTE_RUN}+ words that "
          f"appears word for word in its fact sheet. `mostly_pasted` = paste of {MOSTLY_PASTED:.0%} or more. "
          "`new_words` = share of content words that are not in the fact sheet.\n\n",
          md_table(pct_table(d, "condition", ["paste", "mostly_pasted", "new_words", "words"]), P, N)]
    s += ["\nPaste by model and prompt:\n", md_table(wide(d, "paste"), P, N)]
    s += ["\nNew words by model and prompt:\n", md_table(wide(d, "new_words"), P, N)]
    s += ["\nMostly pasted copies by model and prompt:\n", md_table(wide(d, "mostly_pasted"), P, N)]
    cd = r[r.condition.isin(["C_whitelist", "D_reinject"])]
    m = cd.groupby("model").agg(nothing_added=("claims", lambda x: (x == 0).mean()), paste=("paste", "mean"))
    m = m[m.index.isin(plotted)]
    s += [f"\nUnder the facts-only prompts (C and D), across the {len(m)} plotted models, the rank correlation between "
          f"\"nothing added\" and paste is {m.nothing_added.corr(m.paste, method='spearman'):.2f}. "
          f"Within prompt C, copies with nothing added are {r[(r.condition == 'C_whitelist') & (r.claims == 0)].paste.mean():.1%} "
          f"pasted and copies with a claim {r[(r.condition == 'C_whitelist') & (r.claims > 0)].paste.mean():.1%}.\n"]

    s += ["\n## 3. Sameness (*text only*), share of copies\n",
          "`excited` = excited / thrilled / proud / delighted in the first 260 characters. "
          "`open_to` = \"would you be open\", \"are you open\" or \"open to a\". `n_minute` = a call length such as "
          "\"15-minute\". `placeholder` = a bracket such as [First Name].\n"]
    for ct, cols in [("linkedin", ["excited", "emoji", "hashtag", "em_dash"]),
                     ("cold_email", ["open_to", "n_minute", "placeholder", "em_dash"]), ("hero", ["em_dash"])]:
        s += [f"\n{ct}:\n", md_table(pct_table(d[d.copy_type == ct], "condition", cols), P, N)]
    s += ["\nAll copy types:\n", md_table(pct_table(d, "condition", ["em_dash", "exclamation", "emoji"]), P, N)]
    li = d[(d.copy_type == "linkedin") & (d.condition == "A_none")]
    s += ["\nLinkedIn posts with no instruction that open with excited / thrilled / proud / delighted, by model:\n",
          md_table(pct_table(li, "model", ["excited"]).sort_values("excited", ascending=False), P, N)]
    s += ["\nEm dash by model and prompt:\n", md_table(wide(d, "em_dash"), P, N)]
    s += [f"\n{SHARED_RUN}-word sequences (company name masked) written for 15 or more of the 20 companies:\n",
          md_table(shared_sequences(masked))]

    s += ["\n## 4. Did the number ban move numbers into vague words? (*text only*)\n",
          "`new_numbers` = numbers in the copy that are not in the fact sheet, per copy. `vague` = vague quantity "
          "words per copy (dozens, countless, instantly, every, ...).\n\n",
          md_table(pct_table(d, "condition", ["new_numbers", "vague"]), P, N)]

    core = r[(r.pair <= CORE_PAIRS) & (r.condition == "C_whitelist")]
    t = core.groupby("model").agg(n=("claims", "size"), nothing_added=("claims", lambda x: (x == 0).mean()),
                                  hard_claim=("hard_claim", "mean"), paste=("paste", "mean"),
                                  new_words=("new_words", "mean")).reset_index()
    s += [f"\n## 5. Per model with the facts-only line (prompt C), pairs 1 to {CORE_PAIRS}\n",
          md_table(t.sort_values("nothing_added", ascending=False), P + ["nothing_added"], N)]

    core_all = r[r.pair <= CORE_PAIRS]
    t = core_all.groupby("model").agg(n=("claims", "size"), nothing_added=("claims", lambda x: (x == 0).mean()),
                                      hard_claim=("hard_claim", "mean")).reset_index()
    s += [f"\nAll four prompts, pairs 1 to {CORE_PAIRS}:\n",
          md_table(t.sort_values("hard_claim"), P + ["nothing_added"], N)]

    named = ["rd_team", "rd_clients", "rd_awards", "rd_superlatives"]
    h2 = compare(analyze_load()[0], "A_none", "B_ban", named, -1, "B - A").query("scope == 'all models'")
    s += ["\n## 6. H2 with only the kinds named in the pre-registered text (team, clients, awards, superlatives)\n",
          "The registered analysis also counts `features` among the other kinds. Claims per copy, number ban minus "
          "no instruction; `supported` here means the other kinds fell, which is the opposite of what H2 predicted.\n\n",
          md_table(h2, (), ["diff", "lo", "hi"])]

    a_c = ["A_none", "C_whitelist"]
    tok = d.pivot_table(index="model", columns="condition", values="out_tokens")[a_c]
    cost = d.pivot_table(index="model", columns="condition", values="writer_cost")[a_c]
    clean = r.assign(clean=r.claims == 0).pivot_table(index="model", columns="condition", values="clean")[a_c]
    paste = d.pivot_table(index="model", columns="condition", values="paste")[a_c]
    t = pd.DataFrame({
        "tokens_A": tok["A_none"].round(0), "tokens_C": tok["C_whitelist"].round(0),
        "tokens_C_over_A": (tok["C_whitelist"] / tok["A_none"]).round(2),
        "cost_C_over_A": (cost["C_whitelist"] / cost["A_none"]).round(2),
        "nothing_added_gain": clean["C_whitelist"] - clean["A_none"],
        "paste_gain": paste["C_whitelist"] - paste["A_none"]})
    t = t[t.index.isin(plotted)].sort_values("tokens_C_over_A", ascending=False).reset_index()
    s += ["\n## 7. Does the facts-only line make a model think more? (writer output tokens per copy)\n",
          "Output tokens include the visible text (about 130 to 200 tokens), so anything far above that is hidden "
          "reasoning. `nothing_added_gain` and `paste_gain` are the change from prompt A to prompt C.\n\n",
          md_table(t, P + ["nothing_added_gain", "paste_gain"], ["tokens_C_over_A", "cost_C_over_A"]),
          f"\nRank correlation of the token ratio with the gain in nothing added: "
          f"{t.tokens_C_over_A.corr(t.nothing_added_gain, method='spearman'):.2f}; with the rise in paste: "
          f"{t.tokens_C_over_A.corr(t.paste_gain, method='spearman'):.2f} ({len(t)} models).\n"]

    gens = ["gemini-2.5-flash", "gemini-3.7-flash", "gemini-3.8-flash", "claude-sonnet-4-5", "claude-sonnet-5"]
    g = clean.reindex(gens).reset_index()
    s += ["\n## 8. Generations (H5-b, measured without a predicted direction): share of copies with nothing added\n",
          md_table(g, P, N)]

    r_ac = r[r.condition.isin(a_c)]
    s += ["\n## 9. By kind of text, prompts A and C\n",
          md_table(r_ac.assign(nothing_added=r_ac.claims == 0).groupby(["condition", "copy_type"])
                   .agg(n=("claims", "size"), nothing_added=("nothing_added", "mean"), hard_claim=("hard_claim", "mean"),
                        claims=("claims", "mean")).reset_index(), P + ["nothing_added"], N)]

    numbers = collections.Counter(n for x in d[d.condition == "A_none"].made_up_numbers.dropna() for n in x.split())
    s += ["\n## 10. Most common numbers that are not in the fact sheet, prompt A (*text only*)\n",
          ", ".join(f"{n} ({k}x)" for n, k in numbers.most_common(10)) + "\n"]

    solo, mail, long_ = d[d.team_type == "solo"], d[d.copy_type == "cold_email"], d[d.copy_type != "hero"]
    k = solo.groupby("condition").no_employees.agg(["sum", "size"])
    q = mail.groupby("condition").no_invite.agg(["sum", "size"])
    d[d.no_invite][["model", "company", "condition", "closing"]].to_csv(OUT / "extra_no_invitation.csv", index=False)
    s += ["\n## 11. What else the facts-only line changes (*text only*)\n",
          "`no_employees` = a copy about a one-founder company says it has no employees (its fact sheet says \"One "
          "founder. No employees.\"). `fields_used` = how many of the six fact-sheet fields besides the name show up "
          "(rough word match). `asks_talk` = a recognized request/offer cue in a sentence that also names a "
          "conversation. `invites_only` = another recognized request/offer cue. Rules are in `invitations.py`, "
          "version invitation-cues-2, applied to the full body, excluding subject lines. Product nouns and "
          "question marks alone do not count. `no_invite` = no recognized cue, not proof of no invitation. "
          f"`repeat_pct` = percent of a copy's {REPEAT_RUN}-word "
          "sequences that occur more than once in it. `in_limit` = the copy is inside the word range the request "
          "asked for (LinkedIn 120 to 180, cold email 100 to 150, counted with the subject line).\n",
          "\nOne-founder companies, all three kinds of text ("
          + ", ".join(f"{PROMPT[c]}: {int(k.loc[c, 'sum'])} of {int(k.loc[c, 'size'])}" for c in CONDITIONS) + "):\n",
          md_table(pct_table(solo, "condition", ["no_employees"]), P, N),
          "\nThe same, by kind of text:\n",
          md_table(solo.pivot_table(index="copy_type", columns="condition", values="no_employees")
                   .reindex(columns=CONDITIONS).reset_index(), P, N),
          "\nThe same, by model:\n",
          md_table(wide(solo, "no_employees").sort_values("C_whitelist", ascending=False), P, N),
          "\nCold emails (with no recognized invitation cue: "
          + ", ".join(f"{PROMPT[c]} {int(q.loc[c, 'sum'])} of {int(q.loc[c, 'size'])}" for c in CONDITIONS) + "):\n",
          md_table(pct_table(mail, "condition", ["asks_talk", "invites_only", "no_invite"]), P, N),
          "\nCold emails that ask for a conversation, by model:\n",
          md_table(wide(mail, "asks_talk").sort_values("C_whitelist"), P, N),
          "\nCold emails with no recognized invitation cue, by model:\n",
          md_table(wide(mail, "no_invite").sort_values("C_whitelist", ascending=False), P, N),
          "\nEmails with no recognized cue are listed with closing excerpts in `extra_no_invitation.csv`.\n",
          "\nCold emails and LinkedIn posts:\n",
          md_table(pct_table(long_, "condition", ["fields_used", "repeat_pct", "in_limit", "too_long"]), P, N),
          "\nFact-sheet fields used, by model:\n",
          md_table(wide(long_, "fields_used").sort_values("C_whitelist", ascending=False), (), CONDITIONS),
          f"\nPercent of {REPEAT_RUN}-word sequences repeated inside one copy, by model:\n",
          md_table(wide(long_, "repeat_pct").sort_values("C_whitelist", ascending=False), (), CONDITIONS),
          "\nInside the requested word range, by model, all four prompts:\n",
          md_table(pct_table(long_, "model", ["in_limit", "too_long"]).sort_values("in_limit", ascending=False), P, N)]

    alone = r[r.condition == "A_none"].groupby("model").agg(hard_claim=("hard_claim", "mean"), claims=("claims", "mean"))
    alone.insert(0, "tokens_A", tok["A_none"].round(0))
    alone = alone[alone.index.isin(plotted)].sort_values("tokens_A", ascending=False).reset_index()
    inside = []
    for m in t[t.tokens_C_over_A >= 2].model:
        g = d[(d.model == m) & (d.condition == "C_whitelist")].dropna(subset=["out_tokens"])
        rho = [x.out_tokens.corr(x.paste, method="spearman") for _, x in g.groupby("copy_type")]
        inside.append({"model": m, "n": len(g), "tokens_vs_paste": np.mean(rho)})
    s += ["\n## 12. Two checks on the thinking pattern in section 7\n",
          "With no instruction, do the models that produce more tokens invent less?\n\n", md_table(alone, P, N),
          f"\nRank correlation across these {len(alone)} models: tokens with the share of copies that have a hard "
          f"claim {alone.tokens_A.corr(alone.hard_claim, method='spearman'):+.2f}; with claims per copy "
          f"{alone.tokens_A.corr(alone.claims, method='spearman'):+.2f}.\n",
          "\nInside one model, with the facts-only line: are the copies it spent more tokens on pasted more? "
          "(rank correlation within each kind of text, averaged; models whose tokens at least doubled)\n\n",
          md_table(pd.DataFrame(inside), (), ["tokens_vs_paste"])]

    r = r.assign(nothing_added=(r.claims == 0).astype(float), checks=passes_checks(r).astype(float),
                 concrete=r.concrete.astype(float))
    r = r.assign(both=r.nothing_added * r.checks)
    s += ["\n## 13. Nothing added AND passes four extra checks\n",
          f"`checks` = four automatic checks, chosen after seeing the data: under {MOSTLY_PASTED:.0%} pasted, under "
          f"{CHECK_REPEAT:.0f}% repeated {REPEAT_RUN}-word sequences, does not say \"no employees\", and a cold email "
          "has a recognized invitation cue (`no_invite` is false). Nobody rated the copies; this is not a measure of quality or of "
          "what would sell. `nothing_added` is what the Kaggle task counts (the reader found no claim). `both` = "
          "nothing added and passes the checks. Read copies only.\n\n",
          md_table(pct_table(r, "condition", ["nothing_added", "checks", "both"]), P, N),
          "\nChange between prompts, all models, same model, company and copy type (95% CI from resampling "
          "companies):\n",
          md_table(pd.DataFrame([pooled_gain(r, col, a, b)
                                 for a, b in [("A_none", "B_ban"), ("A_none", "C_whitelist"), ("B_ban", "C_whitelist")]
                                 for col in ["nothing_added", "both"]]), P, N),
          "\n`nothing_added` by model and prompt, all 20 companies:\n", md_table(wide(r, "nothing_added"), P, N),
          "\n`both` by model and prompt, all 20 companies:\n", md_table(wide(r, "both"), P, N),
          f"\n`both`, facts-only line minus number ban inside each model (models with at least {MIN_PLOTTED} "
          "pairs):\n", md_table(paired_gain(r, "both", "B_ban", "C_whitelist"), P, N)]
    clean_c = r[(r.condition == "C_whitelist") & (r.claims == 0)]
    fails = {"at least half pasted": clean_c.paste >= MOSTLY_PASTED, "repeats itself": clean_c.repeat_pct >= CHECK_REPEAT,
             "says no employees": clean_c.no_employees, "cold email with no recognized invitation cue": clean_c.no_invite}
    s += [f"\nOf the {len(clean_c)} copies with nothing added under the facts-only line, "
          f"{1 - passes_checks(clean_c).mean():.1%} fail at least one check: "
          + ", ".join(f"{k} {v.mean():.1%}" for k, v in fails.items()) + " (a copy can fail more than one).\n"]

    core = r[r.pair <= CORE_PAIRS]
    rows = []
    for m, g in core.groupby("model"):
        if len(g) < MIN_RANKED:
            continue
        est, lo, hi, n = boot(g.both, g.company)
        rows.append({"model": m, "n": n, "nothing_added": g.nothing_added.mean(), "both": est, "lo": lo, "hi": hi})
    board = pd.DataFrame(rows)
    board.insert(3, "place", board.nothing_added.rank(ascending=False, method="min").astype(int))
    board["place_both"] = board.both.rank(ascending=False, method="min").astype(int)
    board = board.sort_values("place").reset_index(drop=True)
    s += [f"\nCounted again by model: pairs 1 to {CORE_PAIRS} (12 companies), all four prompts (`lo`, `hi` = 95% CI "
          "of `both`). The Kaggle leaderboard uses all 20 companies, so its numbers differ:\n", md_table(board, P, N)]
    pairs = [("gemini-3.8-flash", "gpt-5.4-nano"), ("gemini-3.7-flash", "gpt-5.4-nano"),
             ("gemini-3.8-flash", "claude-sonnet-5"), ("gpt-5.4", "gemini-3.8-flash"), ("gpt-5.4", "gpt-5.4-nano")]
    s += ["\nDifferences between models on the same company, copy type and prompt:\n",
          md_table(pd.DataFrame([between(core, a, b, col) for a, b in pairs for col in ["nothing_added", "both"]]),
                   P, N)]
    full = board[board.n >= 100].model
    same = core[core.model.isin(full)].pivot_table(index=["company", "copy_type", "condition"], columns="model",
                                                    values=["nothing_added", "both"], aggfunc="first").dropna()
    common = pd.DataFrame({"nothing_added": same["nothing_added"].mean(), "both": same["both"].mean()})
    s += [f"\nOnly the {len(same)} items that every one of the {len(full)} models with at least 100 read copies has:\n",
          md_table(common.sort_values("nothing_added", ascending=False).reset_index(), P, N)]
    ranked = core[core.model.isin(board.model)]
    variants = {}
    for pm in (0.4, 0.5, 0.6):
        for rm in (3.0, 5.0):
            for ask in (True, False):
                for staff in (True, False):
                    ok = passes_checks(ranked, pm, rm, ask, staff)
                    variants[(pm, rm, ask, staff)] = (ranked.nothing_added * ok).groupby(ranked.model).mean().rank(
                        ascending=False, method="min")
    v = pd.DataFrame(variants)
    sens = pd.DataFrame({"place": board.set_index("model").place, "best_place": v.min(axis=1).astype(int),
                         "worst_place": v.max(axis=1).astype(int),
                         "times_first": (v == 1).sum(axis=1)}).sort_values("place").reset_index()
    s += [f"\nThe same table under {v.shape[1]} versions of the checks (pasted cut-off 40 / 50 / 60%, repeat cut-off "
          "3 / 5%, with and without the invitation check, with and without the no-employees check). This varies my "
          "own cut-offs; it is not a validation against people:\n", md_table(sens, P, N)]

    tot = r[["n_numbers", "n_digit", "n_figures"]].sum().astype(int)
    kc = r.groupby("condition").concrete.agg(["sum", "size"]).astype(int)
    ka = r[r.condition == "A_none"].groupby("model").concrete.agg(["sum", "size"]).astype(int).sort_values("sum")
    s += ["\n## 14. Reader flags filtered to digits or clients (exploratory)\n",
          "`concrete` = the reader listed a customer, or a number written with digits that is not only the length of "
          "a call (\"a 15-minute call\"). `hard_claim` in section 1 is wider: of the reader's "
          f"{tot.n_numbers} `numbers` claims only {tot.n_digit} contain a digit, and {tot.n_figures} are left after "
          "dropping call lengths. Non-digit flags include vague quantities such as \"most clinics\" and \"in seconds\". "
          "These categories and filters have not been human-validated; they are not verified fabrications.\n\n",
          md_table(pct_table(r, "condition", ["hard_claim", "concrete"]), P, N),
          "\nCopies with a digit-or-clients reader flag: "
          + ", ".join(f"{PROMPT[c]} {kc.loc[c, 'sum']} of {kc.loc[c, 'size']}" for c in CONDITIONS) + ".\n",
          "\nBy kind of text, no instruction:\n",
          md_table(pct_table(r[r.condition == "A_none"], "copy_type", ["concrete"]), P, N),
          "\nBy model and prompt:\n", md_table(wide(r, "concrete").sort_values("A_none"), P, N),
          "\nNo instruction, copies with a digit-or-clients reader flag by model: "
          + ", ".join(f"{m} {row['sum']} of {row['size']}" for m, row in ka.iterrows()) + ".\n",
          "\nDifference between two models with no instruction, same company and copy type:\n",
          md_table(pd.DataFrame([between(r[r.condition == "A_none"], "claude-sonnet-4-5", "gpt-5.4-nano", "concrete"),
                                 between(r[r.condition == "A_none"], "claude-sonnet-5", "gpt-5.4", "concrete")]), P, N)]

    made = charts(d, plotted, board)
    s += ["\n## Charts\n"] + [f"- `{x}`\n" for x in made]
    s += [f"\nModels drawn in the charts (at least {MIN_PLOTTED} read copies under both prompts and ranked): "
          + ", ".join(plotted) + "\n"]
    (OUT / "extra.md").write_text("".join(s), encoding="utf-8")
    print(f"wrote {OUT / 'extra.md'} and {len(made)} charts; plotted models: {', '.join(plotted)}")


if __name__ == "__main__":
    main()
