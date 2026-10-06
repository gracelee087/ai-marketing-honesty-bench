"""Render actual follow-up results only; does not fabricate or impute missing outputs."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent


def main():
    out = HERE / "out"
    d = pd.read_csv(out / "conditions.csv").set_index("condition").loc[["A", "C", "E"]]
    colors = ["#536476", "#ad754b", "#0a8077"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "figure.facecolor": "#faf9f5",
                         "axes.facecolor": "#faf9f5", "text.color": "#172b38", "axes.labelcolor": "#172b38",
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4))
    labels = ["A\nNo instruction", "C\nFacts only", "E\nFacts + selection"]
    for ax, column, title in [(axes[0], "clean_share", "No unsupported claim identified by glm-5"),
                              (axes[1], "mean_overlap", "Mean word overlap with the fact sheet")]:
        vals = d[column] * 100
        ax.bar(range(3), vals, color=colors, width=.58)
        ax.set_xticks(range(3), labels)
        ax.set_ylim(0, 112)
        ax.set_yticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
        ax.set_title(title, fontsize=12, pad=16)
        for i, (condition, row) in enumerate(d.iterrows()):
            note = f"{row[column]:.1%}"
            if column == "clean_share":
                note += f"\n{int(row.clean_n)}/{int(row.read)} scored"
            else:
                note += f"\nn={int(row.generated)} generated"
            ax.text(i, vals.iloc[i] + 2, note, ha="center", va="bottom", fontsize=10)
        ax.grid(axis="y", color="#dfe3df", linewidth=.6)
        ax.set_axisbelow(True)
    fig.suptitle("One added sentence, tested on ten new companies", fontsize=20, fontweight="bold", y=.98)
    fig.text(.5, .04, "Four selected models · cold emails only · capped outputs · descriptive available-case means · no human ratings",
             ha="center", fontsize=9.5)
    fig.subplots_adjust(top=.80, bottom=.21, left=.07, right=.98, wspace=.25)
    fig.savefig(out / "followup.png", dpi=180)
    plt.close(fig)
    print(out / "followup.png")


if __name__ == "__main__":
    main()
