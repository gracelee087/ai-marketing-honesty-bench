"""English, beginner-friendly submission figures from frozen analysis tables.

python analysis/design_submission_figures.py
Exports PNG and vector SVG. No model calls; no statistical estimates changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import findfont
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/analysis"
FOLLOWUP = ROOT / "validation_2026-10-05/out"
OUT = BASE / "hypothesis_views"
INPUTS = [BASE / "article_prompt_evidence.csv", BASE / "h1.csv",
          BASE / "hypotheses_h2_h4.csv", BASE / "h5_core.csv",
          FOLLOWUP / "conditions.csv", FOLLOWUP / "contrasts.csv"]
PAPER, WHITE, NAVY = "#F7F8FC", "#FFFFFF", "#111B32"
INK, MUTED, LINE = "#19243A", "#637187", "#DCE2EC"
BLUE, MINT, SLATE, LAVENDER = "#4D58E8", "#67E3C5", "#7D8A9D", "#A6AFF7"
TEAL = "#087D70"


def setup():
    try:
        findfont("Segoe UI", fallback_to_default=False)
        family = "Segoe UI"
    except ValueError:
        family = "DejaVu Sans"
    plt.rcParams.update({"font.family": family, "font.size": 12,
        "figure.facecolor": PAPER, "axes.facecolor": PAPER,
        "text.color": INK, "axes.labelcolor": MUTED, "xtick.color": MUTED,
        "ytick.color": MUTED, "axes.unicode_minus": True,
        "svg.fonttype": "path", "savefig.facecolor": PAPER})


def text(fig, x, y, value, size=12, color=INK, weight="normal", **kw):
    return fig.text(x, y, value, fontsize=size, color=color, weight=weight,
                    ha=kw.pop("ha", "left"), va=kw.pop("va", "center"), **kw)


def rect(fig, x, y, w, h, color, z=-5):
    patch = Rectangle((x, y), w, h, facecolor=color, edgecolor="none",
                      transform=fig.transFigure, zorder=z)
    fig.add_artist(patch)


def rule(fig, x1, x2, y, color=LINE, lw=1):
    fig.add_artist(Line2D([x1, x2], [y, y], transform=fig.transFigure,
                         color=color, linewidth=lw, zorder=0))


def frame(number, title, subtitle, size=(14, 9.5), header_bottom=.70):
    fig = plt.figure(figsize=size)
    rect(fig, 0, header_bottom, 1, 1 - header_bottom, NAVY, z=-10)
    rect(fig, .055, .94, .034, .004, MINT, z=1)
    text(fig, .105, .942, "AI MARKETING COPY  /  THE EXPERIMENT", 10, "#BFCAE0", "bold")
    text(fig, .945, .942, number, 12, MINT, "bold", ha="right")
    text(fig, .055, .848, title, 33, WHITE, "bold", linespacing=1.12)
    if subtitle:
        text(fig, .055, header_bottom + .035, subtitle, 11.5, "#BFCAE0")
    return fig


def footer(fig, lines):
    rule(fig, .055, .945, .097)
    for i, line in enumerate(lines):
        text(fig, .055, .069 - i * .023, line, 9.3, MUTED)


def save(fig, name):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist in fig.findobj(matplotlib.text.Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        bb = artist.get_window_extent(renderer)
        if bb.width and bb.height and (bb.x0 < -2 or bb.y0 < -2
                or bb.x1 > fig.bbox.width + 2 or bb.y1 > fig.bbox.height + 2):
            raise ValueError(f"Text outside canvas in {name}: {artist.get_text()}")
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"{name}_en.{suffix}", dpi=220)
    plt.close(fig)


def conditions(prompt, h1):
    fig = frame("01", "Better instructions.\nFewer added claims.",
                "11 AI models  /  20 fictional companies  /  3 writing formats")
    a, c = prompt.iloc[0], prompt.iloc[2]
    text(fig, .66, .86, f"{a.clean_share:.0%} → {c.clean_share:.0%}", 37, MINT, "bold")
    text(fig, .66, .805, "AI checker pass rate", 14, WHITE, "bold")
    text(fig, .66, .772, "No extra rule → use only given facts", 11, "#BFCAE0")
    text(fig, .055, .653, "HOW OFTEN DID THE TEXT PASS?", 11, BLUE, "bold")
    text(fig, .055, .612, "Pass = the AI checker found no claims beyond the supplied facts.", 13)

    ax = fig.add_axes([.10, .285, .845, .28])
    ax.set_facecolor(PAPER)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 84)
    ax.set_xlim(-.6, 3.6)
    ax.set_yticks([0, 25, 50, 75], ["0%", "25%", "50%", "75%"])
    ax.yaxis.grid(True, color=LINE, linewidth=.8)
    ax.tick_params(length=0, pad=10, labelsize=11)
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    vals = prompt.clean_share.to_numpy() * 100
    ax.bar(range(4), vals, width=.62, color=[SLATE, LAVENDER, BLUE, NAVY], zorder=3)
    names = ["No extra rule", "Don't invent numbers", "Use only given facts", "Facts + repeat the brief"]
    for i, row in enumerate(prompt.itertuples()):
        value = row.clean_share * 100
        ax.text(i, value + 9, f"{value:.1f}%", ha="center", va="center",
                fontsize=23, weight="bold", color=BLUE if i == 2 else INK)
        ax.text(i, value + 3, f"{row.reader_clean:,} of {row.read:,} texts", ha="center",
                va="center", fontsize=10, color=MUTED)
        fx = .10 + .845 * ((i + .6) / 4.2)
        text(fig, fx, .247, names[i], 12.5, BLUE if i == 2 else INK, "bold", ha="center")
    rect(fig, .055, .125, .89, .072, "#EAEFFD")
    text(fig, .075, .16, "THE TAKEAWAY", 10, BLUE, "bold")
    text(fig, .245, .16, "Facts-only instructions helped. Repeating the facts had an uncertain extra benefit.", 12)
    footer(fig, [
        "Available first-repeat texts; missing judgments excluded. Bars are descriptive totals, not paired effect estimates.",
        "Checker: glm-5. Passing means no claim was flagged; it does not establish truth or marketing quality.",
    ])
    save(fig, "01_conditions")


def axis_line(fig, x0, x1, bottom, top, low, high, ticks):
    def xpos(value):
        return x0 + (value - low) / (high - low) * (x1 - x0)
    for tick in ticks:
        x = xpos(tick)
        fig.add_artist(Line2D([x, x], [bottom, top], transform=fig.transFigure,
            color=INK if tick == 0 else LINE, linewidth=1.1 if tick == 0 else .65,
            linestyle=(0, (3, 3)) if tick == 0 else "-", zorder=0))
        text(fig, x, bottom - .024, f"{tick:g}", 10, MUTED, ha="center")
    return xpos


def interval(fig, xpos, y, estimate, lo, hi, color):
    assert lo <= estimate <= hi
    fig.add_artist(Line2D([xpos(lo), xpos(hi)], [y, y], transform=fig.transFigure,
                          color=color, linewidth=4, solid_capstyle="round", zorder=3))
    for bound in (lo, hi):
        fig.add_artist(Line2D([xpos(bound), xpos(bound)], [y - .006, y + .006],
                              transform=fig.transFigure, color=color, linewidth=1.5, zorder=3))
    fig.add_artist(Line2D([xpos(estimate)], [y], transform=fig.transFigure,
                          marker="o", markersize=10, markeredgewidth=2,
                          markeredgecolor=PAPER, color=color, zorder=4))


def hypotheses(tests, sizes):
    fig = frame("02", "Which changes really helped?", "", (14, 11.5), .78)
    text(fig, .055, .804, "We count claims the company brief does not support.", 12, "#BFCAE0")
    text(fig, .055, .733, "WHAT WE CHANGED", 10.5, MUTED, "bold")
    text(fig, .422, .733, "CHANGE IN CLAIMS PER TEXT", 10.5, MUTED, "bold")
    text(fig, .778, .733, "WHAT HAPPENED", 10.5, MUTED, "bold")

    h2 = tests.loc[tests.test.eq("H2")].iloc[0]
    h3 = tests.loc[tests.test.eq("H3 C-B")].iloc[0]
    h4 = tests.loc[tests.test.eq("H4 D-C")].iloc[0]
    rows = [
        ("Don't invent numbers", "Number claims · vs no extra rule", h2.numbers_diff, h2.numbers_lo, h2.numbers_hi, BLUE, "Clear decrease", h2.n_pairs),
        ("Don't invent numbers", "Other claims · vs no extra rule", h2.others_diff, h2.others_lo, h2.others_hi, BLUE, "Clear decrease", h2.n_pairs),
        ("Use only given facts", "All claims · vs number rule", h3["diff"], h3.lo, h3.hi, TEAL, "Clear decrease", h3.n_pairs),
        ("Repeat the same facts", "All claims · vs facts only", h4["diff"], h4.lo, h4.hi, SLATE, "Unclear", h4.n_pairs),
    ]
    ys = [.659, .559, .459, .359]
    for i, y in enumerate(ys):
        if i % 2 == 0:
            rect(fig, .045, y - .044, .91, .087, "#EDF0F7")
    xpos = axis_line(fig, .425, .735, .305, .704, -1.05, .20, [-1, -.5, 0])
    text(fig, xpos(0), .719, "NO CHANGE", 9, MUTED, "bold", ha="center")
    for y, row in zip(ys, rows):
        name, label, estimate, lo, hi, color, verdict, n = row
        text(fig, .065, y + .016, name, 15, INK, "bold")
        text(fig, .065, y - .015, f"{label}  /  {int(n)} pairs", 10.7, MUTED)
        interval(fig, xpos, y, estimate, lo, hi, color)
        text(fig, .78, y + .025, verdict, 13, color, "bold")
        text(fig, .78, y - .003, f"{abs(estimate):.2f} fewer claims / text", 11.5)
        text(fig, .78, y - .029, f"95% range: {lo:+.2f} to {hi:+.2f}", 9.5, MUTED)
    text(fig, .425, .258, "← Fewer claims", 10, BLUE, "bold")
    text(fig, .735, .258, "More →", 10, MUTED, ha="right")
    text(fig, .055, .225, "READING THE LINES", 10, BLUE, "bold")
    text(fig, .245, .225, "Dot = average change. Line = uncertainty range (95% confidence interval).", 11)
    text(fig, .245, .199, "If the line crosses zero, we cannot establish a clear decrease or increase.", 11)

    # Keep the size result in plain language rather than adding a second dense plot.
    rule(fig, .055, .945, .168)
    text(fig, .055, .142, "AND MODEL SIZE?", 10, BLUE, "bold")
    assert list(sizes.verdict) == ["inconclusive", "inconclusive", "supported"]
    text(fig, .245, .144, "Both OpenAI comparisons were unclear. The Gemini comparison also changed generation.", 11)
    text(fig, .245, .119, "This test cannot tell us whether size alone explains the difference.", 11, MUTED)
    footer(fig, [
        "Instruction tests: matched items across 20 companies. Model-size tests: first 12 companies. Judge: glm-5, not human graders.",
        "Intervals resample companies 10,000 times. H2 was contradicted: banning numbers reduced other unsupported claims too.",
    ])
    save(fig, "02_hypotheses")


def followup(cond, contrasts):
    fig = frame("03", "We tried a fix.\nIt didn't clearly help.",
                "A separate test on new companies; the protocol was fixed before the runs.", (14, 10.5), .72)
    text(fig, .73, .866, "120", 48, MINT, "bold")
    text(fig, .73, .807, "emails generated", 14, WHITE, "bold")
    text(fig, .73, .775, "10 new companies · 4 AI models", 11, "#BFCAE0")
    text(fig, .055, .668, "HOW MUCH WORDING MATCHED THE BRIEF?", 10.5, BLUE, "bold")
    text(fig, .055, .634, "Share of words matching phrases in the company brief.", 12)

    ax = fig.add_axes([.10, .337, .385, .244])
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=LINE, linewidth=.8)
    ax.set_ylim(0, 30)
    ax.set_xlim(-.55, 2.55)
    ax.set_yticks([0, 10, 20, 30], ["0%", "10%", "20%", "30%"])
    ax.set_xticks([])
    ax.tick_params(length=0, pad=10, labelsize=11)
    for spine in ax.spines.values():
        spine.set_visible(False)
    rows = cond.set_index("condition").loc[["A", "C", "E"]]
    values = rows.mean_overlap.to_numpy() * 100
    ax.bar(range(3), values, width=.61, color=[SLATE, BLUE, TEAL], zorder=3)
    labels = ["No extra rule", "Facts only", "Facts only\n+ choose relevant facts"]
    for i, value in enumerate(values):
        ax.text(i, value + 2, f"{value:.1f}%", ha="center", va="center", fontsize=23,
                weight="bold", color=BLUE if i == 1 else INK)
        fx = .10 + .385 * ((i + .55) / 3.1)
        text(fig, fx, .296, labels[i], 11.5, INK, "bold", ha="center", linespacing=1.4)
    text(fig, .11, .248, "40 emails per condition", 10, MUTED)

    text(fig, .56, .668, "WHAT THE PAIRED COMPARISONS SHOW", 10.5, BLUE, "bold")
    comparisons = [("C-A", .601, "Facts only vs no extra rule", "Clear increase in overlap", BLUE),
                   ("E-C", .422, "Extra sentence vs facts only", "No clear reduction", SLATE)]
    for key, top, name, conclusion, color in comparisons:
        r = contrasts.loc[contrasts.contrast.eq(key) & contrasts.measure.eq("overlap")].iloc[0]
        value, lo, hi = r[["difference", "lo", "hi"]].to_numpy(dtype=float) * 100
        text(fig, .56, top, name, 12.5, INK, "bold")
        text(fig, .56, top - .04, f"{value:+.2f}", 28, color, "bold")
        text(fig, .727, top - .044, "percentage points", 11, MUTED)
        text(fig, .56, top - .082, conclusion, 12, color, "bold")
        text(fig, .56, top - .113, f"95% range: {lo:+.2f} to {hi:+.2f} points", 10.5, MUTED)
    rule(fig, .56, .945, .455)
    text(fig, .56, .249, "A range crossing 0 means the change is uncertain.", 10.2, MUTED)

    rect(fig, .055, .133, .89, .086, "#EAEFFD")
    text(fig, .074, .194, "THE EXTRA SENTENCE", 10, BLUE, "bold")
    text(fig, .074, .157,
        '“Select the facts relevant to this audience; you do not need to include every field.”', 13)
    footer(fig, [
        "Overlap counts words in exact four-word matches with the brief; legitimate technical wording also counts. This is not a quality score.",
        "40 matched pairs per comparison; 95% company-bootstrap intervals, 10,000 resamples. Every new brief included a capability limitation.",
    ])
    save(fig, "03_followup")


def main():
    setup()
    OUT.mkdir(exist_ok=True, parents=True)
    prompt, h1, tests, sizes, cond, contrasts = [pd.read_csv(p) for p in INPUTS]
    prompt = prompt.set_index("condition").loc[["A_none", "B_ban", "C_whitelist", "D_reinject"]].reset_index()
    h1 = h1.loc[h1.scope.eq("all models")]
    tests = tests.loc[tests.scope.eq("all models")]
    np.testing.assert_allclose(prompt.reader_clean / prompt.read, prompt.clean_share)
    np.testing.assert_allclose(1 - prompt.iloc[0].clean_share, h1.iloc[0].share_with_claim)
    assert len(tests) == 3 and len(sizes) == 3 and list(cond.generated) == [40, 40, 40]
    for key, (a, b) in {"C-A": ("C", "A"), "E-C": ("E", "C")}.items():
        r = contrasts.loc[contrasts.contrast.eq(key) & contrasts.measure.eq("overlap")].iloc[0]
        means = cond.set_index("condition").mean_overlap
        np.testing.assert_allclose(r.difference, means[a] - means[b])
        assert r.n_pairs == 40 and r.companies == 10
    conditions(prompt, h1)
    hypotheses(tests, sizes)
    followup(cond, contrasts)
    manifest = {"generator": "analysis/design_submission_figures.py",
        "command": "python analysis/design_submission_figures.py", "design": "editorial-v2",
        "language": "en", "new_model_calls": 0,
        "sources": [{"path": p.relative_to(ROOT).as_posix(),
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in INPUTS],
        "figures": {"01_conditions": "Pooled descriptive reader-clean rates, all available first-repeat items.",
                    "02_hypotheses": "Paired H2-H4 estimates and existing 95% intervals; H5 summarized in plain language.",
                    "03_followup": "Overlap across all 120 generated follow-up emails, with paired estimates and existing intervals."},
        "not_visualized": ["H5-b generations", "H6 cost", "S stability"],
        "formats": ["220-dpi PNG", "vector SVG with outlined fonts"],
        "archive": "archive_v1 contains the preceding design and its generator."}
    (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered three English submission figures as PNG + SVG: {OUT}")
    print("Source arithmetic, paired contrasts, interval bounds and canvas text bounds passed.")


if __name__ == "__main__":
    main()
