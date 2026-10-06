"""Render the latest English submission figures, without model calls.

Run: python analysis/visualize_hypotheses.py
Outputs: results/analysis/hypothesis_views/*_en.{png,svg} and provenance.json
The original bilingual layout helpers remain below for historical reference.
The default entry point delegates to the redesigned English-only generator.
Intervals are read from the existing company-bootstrap results, never inferred
from unpaired aggregate bars. This script does not change scores or the article.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "analysis"
FOLLOWUP = ROOT / "validation_2026-10-05" / "out"
OUT = SOURCE / "hypothesis_views"
BG, INK, MUTED, GRID = "#FAF9F5", "#162E3A", "#596B77", "#E2E5E2"
SLATE, BLUE, TEAL, ORANGE = "#70808C", "#487CAE", "#087E78", "#BC703E"
INPUTS = [SOURCE / "article_prompt_evidence.csv", SOURCE / "h1.csv",
          SOURCE / "hypotheses_h2_h4.csv", SOURCE / "h5_core.csv",
          FOLLOWUP / "conditions.csv", FOLLOWUP / "contrasts.csv"]


def choose(lang: str, ko: str, en: str) -> str:
    return ko if lang == "ko" else en


def style(lang: str) -> None:
    family = "DejaVu Sans"
    if lang == "ko":
        # Prefer an installed Korean font; fail clearly instead of drawing tofu.
        for name in ("Malgun Gothic", "Noto Sans CJK KR", "Noto Sans KR", "NanumGothic"):
            try:
                font_manager.findfont(name, fallback_to_default=False)
                family = name
                break
            except ValueError:
                continue
        else:
            raise RuntimeError("A Korean font is needed for the Korean figures.")
    plt.rcParams.update({
        "font.family": family, "font.size": 11, "axes.unicode_minus": False,
        "figure.facecolor": BG, "axes.facecolor": BG,
        "text.color": INK, "axes.labelcolor": MUTED,
        "xtick.color": MUTED, "ytick.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.bottom": False, "axes.spines.left": False,
        "svg.fonttype": "path", "savefig.facecolor": BG,
    })


def heading(fig, eyebrow, title, subtitle):
    fig.text(.055, .95, eyebrow, fontsize=10, color=TEAL, weight="bold")
    fig.text(.055, .89, title, fontsize=23, weight="bold")
    fig.text(.055, .845, subtitle, fontsize=10.5, color=MUTED)


def axis_style(ax):
    ax.tick_params(length=0, pad=8)
    ax.xaxis.grid(True, color=GRID, linewidth=.8)
    ax.set_axisbelow(True)


def save(fig, stem, lang):
    # Saving without a tight bounding box keeps the intended export dimensions.
    # All text must remain inside the canvas; this catches clipped annotations.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist in fig.findobj(matplotlib.text.Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        if box.width and box.height and (box.x0 < -2 or box.y0 < -2
                or box.x1 > fig.bbox.width + 2 or box.y1 > fig.bbox.height + 2):
            raise ValueError(f"Text outside canvas in {stem}_{lang}: {artist.get_text()}")
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"{stem}_{lang}.{suffix}", dpi=200)
    plt.close(fig)


def draw_forest(ax, rows, xlim, ticks, xlabel):
    """Each row: label, estimate, lower, upper, color, explicit interpretation."""
    axis_style(ax)
    ax.axvline(0, color=INK, linewidth=1.1, linestyle=(0, (3, 3)))
    ax.set_xlim(*xlim)
    ax.set_xticks(ticks)
    ax.set_ylim(len(rows) - .4, -.6)
    ax.set_yticks([])
    ax.set_xlabel(xlabel, labelpad=12, fontsize=10)
    for y, (label, estimate, lo, hi, color, interpretation) in enumerate(rows):
        assert lo <= estimate <= hi, (label, estimate, lo, hi)
        ax.errorbar(estimate, y, xerr=[[estimate - lo], [hi - estimate]],
                    fmt="o", color=color, markersize=8, capsize=4,
                    elinewidth=2.5, capthick=1.5, zorder=3)
        ax.text(-.055, y, label, transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=10, linespacing=1.6)
        ax.text(1.055, y - .12, f"{estimate:+.2f}  [{lo:+.2f}, {hi:+.2f}]",
                transform=ax.get_yaxis_transform(), ha="left", va="center",
                fontsize=11, weight="bold", color=color)
        ax.text(1.055, y + .20, interpretation,
                transform=ax.get_yaxis_transform(), ha="left", va="center",
                fontsize=9, color=MUTED)


def conditions(lang, prompt, h1):
    fig = plt.figure(figsize=(12, 7.5))
    heading(fig, "01 / PROMPT CONDITIONS",
            choose(lang, "지시문을 바꾸자, AI 검사 통과율이 달라졌다",
                   "The checker score changed with the instruction"),
            choose(lang, "11개 모델 · 20개 회사 · 3개 글 형식 · 첫 번째 생성 중 평가 가능한 글",
                   "11 models · 20 companies · 3 formats · available reader-scored first-repeat texts"))
    ax = fig.add_axes([.24, .265, .69, .49])
    axis_style(ax)
    labels = choose(lang,
                    "A  제한 없음|B  숫자 금지|C  주어진 사실만|D  C + 사실 반복",
                    "A  No instruction|B  Number ban|C  Facts only|D  C + facts repeated").split("|")
    values = prompt.clean_share.to_numpy() * 100
    ax.barh(range(4), values, height=.54, color=[SLATE, BLUE, TEAL, ORANGE])
    ax.set_yticks(range(4), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel(choose(lang, "근거 없는 주장이 발견되지 않은 글 (%)",
                        "Texts with zero unsupported claims identified (%)"), labelpad=12)
    for y, r in enumerate(prompt.itertuples()):
        ax.text(r.clean_share * 100 + 1.5, y - .075, f"{r.clean_share:.1%}",
                fontsize=16, weight="bold", va="center")
        ax.text(r.clean_share * 100 + 1.5, y + .18,
                f"{int(r.reader_clean):,} / {int(r.read):,}", fontsize=10, color=MUTED, va="center")
    claim = h1.iloc[0]
    fig.text(.055, .145, choose(lang,
        f"H1 지지: 제한이 없을 때 {claim.share_with_claim:.1%}에서 근거 없는 주장이 발견됨.",
        f"H1 supported: without an instruction, {claim.share_with_claim:.1%} contained an unsupported claim."),
        fontsize=12, weight="bold")
    fig.text(.055, .080, choose(lang,
        "평가자: glm-5. 사람 검증이나 마케팅 품질 점수가 아님. 결측 응답은 제외함.\n막대는 가용 표본의 합산 비율이며, 지시문 간 검정은 별도의 짝지은 비교를 사용함.",
        "Judge: glm-5; not human-verified truth or marketing quality. Missing judgments are excluded.\nBars are pooled descriptive proportions; inference uses separate paired comparisons."),
        fontsize=9, color=MUTED, linespacing=1.8)
    save(fig, "01_conditions", lang)


def hypotheses(lang, tests, sizes):
    fig = plt.figure(figsize=(13.5, 11))
    heading(fig, "02 / HYPOTHESIS TESTS",
            choose(lang, "확인된 효과와 불확실한 효과를 구분하기",
                   "Separate supported effects from uncertain ones"),
            choose(lang, "점 = 평균 변화량 · 선 = 95% 회사 단위 부트스트랩 신뢰구간 · 점선 = 변화 없음",
                   "Dot = mean change · line = 95% company-bootstrap interval · dashed line = no change"))
    h2 = tests.loc[tests.test.eq("H2")].iloc[0]
    h3 = tests.loc[tests.test.eq("H3 C-B")].iloc[0]
    h4 = tests.loc[tests.test.eq("H4 D-C")].iloc[0]
    pair = choose(lang, "쌍", " pairs")
    prompt_rows = [
        (choose(lang, "H2 · 숫자 주장", "H2 · Numeric claims") + f"\nB - A · {int(h2.n_pairs)}{pair}",
         h2.numbers_diff, h2.numbers_lo, h2.numbers_hi, BLUE,
         choose(lang, "숫자 금지 후 감소", "Reduced after the number ban")),
        (choose(lang, "H2 · 숫자 외 주장", "H2 · Other claims") + f"\nB - A · {int(h2.n_pairs)}{pair}",
         h2.others_diff, h2.others_lo, h2.others_hi, ORANGE,
         choose(lang, "H2 기각: 다른 주장도 감소", "H2 falsified: other claims fell too")),
        (choose(lang, "H3 · 사실만 vs 숫자 금지", "H3 · Facts only vs number ban") + f"\nC - B · {int(h3.n_pairs)}{pair}",
         h3["diff"], h3.lo, h3.hi, TEAL,
         choose(lang, "H3 지지: 추가 감소", "H3 supported: a further reduction")),
        (choose(lang, "H4 · 사실 반복 추가", "H4 · Repeat the facts") + f"\nD - C · {int(h4.n_pairs)}{pair}",
         h4["diff"], h4.lo, h4.hi, SLATE,
         choose(lang, "H4 판단 유보: 0을 포함", "H4 inconclusive: interval includes 0")),
    ]
    fig.text(.055, .785, choose(lang, "지시문 효과  /  20개 회사의 가용 표본",
                              "Instruction effects  /  available items from 20 companies"), fontsize=12, weight="bold")
    ax = fig.add_axes([.325, .505, .375, .245])
    draw_forest(ax, prompt_rows, (-1.08, .18), [-1, -.75, -.5, -.25, 0],
                choose(lang, "근거 없는 주장 수 변화 / 글  ·  왼쪽 = 감소",
                       "Change in claims per text  ·  left = fewer"))
    fig.text(.055, .405, choose(lang, "H5 · 작은 모델 - 큰 모델  /  첫 12개 회사",
                              "H5 · Smaller minus larger model  /  first 12 companies"), fontsize=12, weight="bold")
    labels = ["gpt-5.4-nano - gpt-5.4", "gpt-oss-20b - gpt-oss-120b",
              "gemini-3.1-flash-lite\n- gemini-3.8-flash"]
    size_rows = []
    for i, row in enumerate(sizes.itertuples()):
        size_rows.append((labels[i] + f"\n{row.n_pairs}{pair}", row.diff, row.lo, row.hi,
            TEAL if row.verdict == "supported" else SLATE,
            choose(lang, "지지, 단 세대 차이가 섞여 있음", "Supported; generation is confounded")
            if row.verdict == "supported" else choose(lang, "판단 유보", "Inconclusive")))
    ax = fig.add_axes([.325, .17, .375, .20])
    draw_forest(ax, size_rows, (-1.6, 1.05), [-1.5, -1, -.5, 0, .5, 1],
                choose(lang, "주장 수 차이 / 글  ·  오른쪽 = 작은 모델이 더 많음",
                       "Claims per text  ·  right = more in the smaller model"))
    fig.text(.055, .070, choose(lang,
        "동일 모델·회사·글 형식의 조건 비교 또는 동일 항목의 모델 비교. 회사 단위 10,000회 재표집.\n신뢰구간이 0을 포함하면 방향을 확정하지 않음. glm-5 판정이며 사람 평가가 아님.",
        "Matched conditions or model outputs; companies resampled 10,000 times.\nAn interval crossing zero leaves the direction unresolved. Scores are from glm-5, not human grading."),
        fontsize=9, color=MUTED, linespacing=1.8)
    save(fig, "02_hypotheses", lang)


def followup(lang, cond, contrasts):
    fig = plt.figure(figsize=(13, 8.5))
    heading(fig, "03 / NEW-COMPANY FOLLOW-UP",
            choose(lang, "원문 중첩은 늘었고, 추가 문장의 개선은 불확실했다",
                   "Overlap rose; the extra sentence did not clearly help"),
            choose(lang, "새 회사 10개 · 모델 4개 · 조건 3개 · 이메일 120개 · 실행 전 고정한 후속 실험",
                   "10 new companies · 4 writers · 3 conditions · 120 emails · protocol frozen before runs"))
    fig.text(.055, .765, choose(lang, "원문과 겹치는 단어의 평균 비율", "Mean share of words overlapping the brief"),
             fontsize=12, weight="bold")
    ax = fig.add_axes([.10, .36, .38, .335])
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRID, linewidth=.8)
    ax.tick_params(length=0, pad=9)
    rows = cond.set_index("condition").loc[["A", "C", "E"]]
    vals = rows.mean_overlap.to_numpy() * 100
    ax.bar(range(3), vals, color=[SLATE, TEAL, ORANGE], width=.60)
    ax.set_ylim(0, 30)
    ax.set_yticks([0, 10, 20, 30], ["0%", "10%", "20%", "30%"])
    ax.set_xticks(range(3), choose(lang, "A\n제한 없음|C\n주어진 사실만|E\nC + 관련 사실 선택",
                                  "A\nNo instruction|C\nFacts only|E\nC + select relevant facts").split("|"))
    for i, value in enumerate(vals):
        ax.text(i, value + 1.1, f"{value:.1f}%", ha="center", weight="bold", fontsize=17)
    fig.text(.545, .765, choose(lang, "동일 항목의 변화량 [95% 신뢰구간]", "Paired change [95% interval]"),
             fontsize=12, weight="bold")
    ax = fig.add_axes([.585, .395, .34, .25])
    axis_style(ax)
    ax.axvline(0, color=INK, linewidth=1.1, linestyle=(0, (3, 3)))
    ax.set_xlim(-4, 20)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.set_ylim(1.55, -.8)
    ax.set_yticks([0, 1], ["C - A", "E - C"])
    ax.set_xlabel(choose(lang, "원문 중첩률 변화 (%p)", "Change in overlap (percentage points)"), labelpad=12, fontsize=10)
    for i, contrast in enumerate(["C-A", "E-C"]):
        row = contrasts.loc[contrasts.contrast.eq(contrast) & contrasts.measure.eq("overlap")].iloc[0]
        value, lo, hi = row[["difference", "lo", "hi"]].to_numpy(dtype=float) * 100
        color = TEAL if i == 0 else SLATE
        ax.errorbar(value, i, xerr=[[value - lo], [hi - value]], fmt="o", color=color,
                    markersize=8, capsize=4, elinewidth=2.5)
        ax.text(.02, i - .40, f"{value:+.2f} [{lo:+.2f}, {hi:+.2f}]", fontsize=11,
                weight="bold", color=color, transform=ax.get_yaxis_transform(),
                bbox={"facecolor": BG, "edgecolor": "none", "pad": 2}, zorder=5)
        text = choose(lang, "중첩 증가 재현 · 40쌍", "Overlap increase replicated · 40 pairs") if i == 0 else choose(
            lang, "개선 여부 불확실 · 40쌍", "Reduction remains uncertain · 40 pairs")
        ax.text(.02, i + .32, text, fontsize=9, color=MUTED, transform=ax.get_yaxis_transform(),
                bbox={"facecolor": BG, "edgecolor": "none", "pad": 2}, zorder=5)
    fig.text(.055, .225, choose(lang,
        'E에서 추가한 문장: “이 독자에게 관련 있는 사실을 고르세요. 모든 항목을 포함할 필요는 없습니다.”',
        'E adds: “Select the facts relevant to this audience; you do not need to include every field.”'), fontsize=11)
    fig.text(.055, .105, choose(lang,
        "각 조건 40개 이메일 모두 생성. 중첩 지표는 생성된 전체 120개를 사용하며 판정기 결측과 무관함.\n회사 단위 10,000회 부트스트랩. 원문 중첩은 정확히 일치하는 4단어 구간으로 측정하며, 정당한 용어 반복도 포함함.\n모든 새 회사 정보에 기능 제한을 넣은 표적 실험임. 중첩률은 마케팅 품질이나 표절 판정이 아님.",
        "40 emails generated per condition; overlap uses all 120 texts, independently of missing reader judgments.\nIntervals resample companies 10,000 times. Exact four-word matches include legitimate terminology.\nAll new briefs contain a capability limitation: a targeted test, not a marketing-quality or plagiarism score."),
        fontsize=9, color=MUTED, linespacing=1.8)
    save(fig, "03_followup", lang)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prompt, h1, tests, sizes, cond, contrasts = [pd.read_csv(p) for p in INPUTS]
    prompt = prompt.set_index("condition").loc[["A_none", "B_ban", "C_whitelist", "D_reinject"]].reset_index()
    h1 = h1.loc[h1.scope.eq("all models")]
    tests = tests.loc[tests.scope.eq("all models")]
    assert len(prompt) == 4 and len(h1) == 1 and len(tests) == 3 and len(sizes) == 3
    np.testing.assert_allclose(prompt.reader_clean / prompt.read, prompt.clean_share)
    np.testing.assert_allclose(1 - prompt.iloc[0].clean_share, h1.iloc[0].share_with_claim)
    assert list(cond.generated) == [40, 40, 40]
    for contrast, (a, b) in {"C-A": ("C", "A"), "E-C": ("E", "C")}.items():
        observed = contrasts.loc[contrasts.contrast.eq(contrast) & contrasts.measure.eq("overlap")].iloc[0]
        by_condition = cond.set_index("condition").mean_overlap
        np.testing.assert_allclose(observed.difference, by_condition[a] - by_condition[b])
        assert observed.n_pairs == 40 and observed.companies == 10
    for lang in ("ko", "en"):
        style(lang)
        conditions(lang, prompt, h1)
        hypotheses(lang, tests, sizes)
        followup(lang, cond, contrasts)
    provenance = {
        "generator": "analysis/visualize_hypotheses.py",
        "command": "python analysis/visualize_hypotheses.py",
        "new_model_calls": 0,
        "sources": [{"path": p.relative_to(ROOT).as_posix(),
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in INPUTS],
        "figures": {"01_conditions": "Descriptive pooled rates; H1 aggregate claim share.",
                    "02_hypotheses": "H2-H4 paired instruction tests; H5 core-company model comparisons.",
                    "03_followup": "All 120 generated follow-up emails; matched overlap contrasts."},
        "intervals": "Existing 95% company-bootstrap results (10,000 resamples), not recomputed.",
        "not_visualized": ["H5-b generation descriptions", "H6 cost correlations", "S repeat stability"],
        "formats": ["200-dpi PNG", "SVG with outlined glyphs"],
        "languages": ["ko", "en"],
    }
    (OUT / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved 6 figures in PNG + SVG: {OUT}")
    print("Validated aggregate counts, matched follow-up differences, interval bounds and text canvas bounds.")


if __name__ == "__main__":
    from design_submission_figures import main as render_submission_figures
    render_submission_figures()
