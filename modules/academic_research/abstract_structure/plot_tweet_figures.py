"""推文图表：由 v03_full_tweet_aggregates.json 生成 6 张中文 PNG（300 dpi）。

运行：
    F:/global_venv/.venv/Scripts/python.exe plot_tweet_figures.py
输出：manuscripts/figures/abstract_structure_tweet/fig1..fig6 PNG。
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AGG_PATH = (
    PROJECT_ROOT / "data" / "processed" / "abstract_structure" / "run_20260909_v03_full"
    / "v03_full_tweet_aggregates.json"
)
OUT_DIR = PROJECT_ROOT / "manuscripts" / "figures" / "abstract_structure_tweet"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# 功能五色固定映射
COLORS = {
    "W": "#4C78A8",  # what 研究内容
    "H": "#F58518",  # how 方法
    "F": "#54A24B",  # findings 结论
    "Y": "#B279A2",  # why 意义
    "O": "#9D9D9D",  # 背景/其他
}
FUNC_LABEL = {"W": "What 研究内容", "H": "How 方法", "F": "Findings 结论", "Y": "Why 意义", "O": "背景/其他"}
JOURNALS = ["AER", "JPE", "ECMA", "REStud", "QJE"]


def save(fig: plt.Figure, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("saved", path)


def fig1_length_by_journal(agg: dict) -> None:
    by = agg["word_count"]["by_journal"]
    meds = np.array([by[j]["median"] for j in JOURNALS])
    p95 = np.array([by[j]["p95"] for j in JOURNALS])
    x = np.arange(len(JOURNALS))
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(x, meds, width=0.55, color="#4C78A8", alpha=0.9)
    ax.scatter(x, p95, marker="_", s=600, linewidths=2.5, color="#E45756", zorder=3)
    ax.set_ylabel("摘要词数")
    ax.set_xticks(x, JOURNALS)
    ax.set_ylim(0, 275)
    ax.set_xlim(-0.6, len(JOURNALS) - 0.4 + 0.6)
    for b, m, hi95 in zip(bars, meds, p95):
        ax.text(b.get_x() + b.get_width() / 2, m / 2, f"{m:.0f}", ha="center", va="center",
                fontsize=11, color="white", fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2 + 0.34, hi95, f"p95={hi95:.0f}",
                ha="left", va="center", fontsize=9, color="#E45756")
    save(fig, "fig1_length_by_journal.png")


def _word_values_by_journal() -> dict[str, list[int]]:
    """从语料台账流式读每篇词数（小提琴/箱线图需要原始分布）。"""
    corpus = (
        PROJECT_ROOT / "data" / "processed" / "abstract_structure" / "run_20260908_a"
        / "corpus_manifest.jsonl"
    )
    sample = PROJECT_ROOT / "data" / "processed" / "abstract_structure" / "run_20260909_v03_full" / "full_sample_manifest.jsonl"
    journal_of = {}
    with open(sample, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                journal_of[r["article_id"]] = r["journal_code"]
    vals: dict[str, list[int]] = {j: [] for j in JOURNALS}
    with open(corpus, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            j = journal_of.get(r["article_id"])
            if j is not None and r["word_count_v1"] is not None:
                vals[j].append(r["word_count_v1"])
    return vals


def fig1_variants(agg: dict) -> None:
    """小提琴图 + 箱线图对比版，供选型；中位数红点、p95 红虚线标注。"""
    by = agg["word_count"]["by_journal"]
    meds = [by[j]["median"] for j in JOURNALS]
    p95 = [by[j]["p95"] for j in JOURNALS]
    vals = _word_values_by_journal()
    data = [vals[j] for j in JOURNALS]
    x = np.arange(1, len(JOURNALS) + 1)

    fig, ax = plt.subplots(figsize=(7, 4))
    parts = ax.violinplot(data, positions=x, showextrema=False, widths=0.7)
    for body in parts["bodies"]:
        body.set_facecolor("#4C78A8")
        body.set_alpha(0.75)
    ax.scatter(x, meds, marker="o", s=40, color="#1a1a1a", zorder=3)
    ax.scatter(x, p95, marker="D", s=35, color="#E45756", zorder=3)
    for xi, m, hi95 in zip(x, meds, p95):
        ax.text(xi + 0.3, m, f"{m:.0f}", ha="left", va="center", fontsize=9)
        ax.text(xi + 0.3, hi95, f"p95={hi95:.0f}", ha="left", va="center", fontsize=9, color="#E45756")
    ax.set_xticks(x, JOURNALS)
    ax.set_ylabel("摘要词数")
    ax.set_ylim(0, 320)
    ax.set_xlim(0.4, len(JOURNALS) + 1.3)
    save(fig, "fig1b_violin.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    bp = ax.boxplot(data, positions=x, widths=0.5, showfliers=False,
                    medianprops=dict(color="#1a1a1a", linewidth=2),
                    boxprops=dict(color="#4C78A8"), whiskerprops=dict(color="#4C78A8"),
                    capprops=dict(color="#4C78A8"))
    ax.scatter(x, p95, marker="D", s=35, color="#E45756", zorder=3)
    for xi, m, hi95 in zip(x, meds, p95):
        ax.text(xi + 0.3, m, f"{m:.0f}", ha="left", va="center", fontsize=9)
        ax.text(xi + 0.3, hi95, f"p95={hi95:.0f}", ha="left", va="center", fontsize=9, color="#E45756")
    ax.set_xticks(x, JOURNALS)
    ax.set_ylabel("摘要词数")
    ax.set_ylim(0, 320)
    ax.set_xlim(0.4, len(JOURNALS) + 1.3)
    save(fig, "fig1c_box.png")


def fig2_sentence_count(agg: dict) -> None:
    ov = agg["sentence_count"]["overall"]["dist_pct"]
    ks = [str(k) for k in range(3, 10)]
    overall = [ov.get(k, 0.0) for k in ks]
    byj = agg["sentence_count"]["by_journal"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 1.5]})
    bars = ax1.bar(ks, overall, color="#4C78A8", width=0.6)
    for b, v in zip(bars, overall):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.0f}%", ha="center", fontsize=9)
    ax1.set_xlabel("摘要句数")
    ax1.set_ylabel("占比")
    ax1.set_ylim(0, 30)

    colors = plt.cm.tab10.colors
    for i, j in enumerate(JOURNALS):
        vals = [byj[j]["dist_pct"].get(k, 0.0) for k in ks]
        ax2.plot(ks, vals, "o-", color=colors[i], lw=1.8, ms=4, label=j)
    ax2.set_xlabel("摘要句数")
    ax2.set_ylabel("占比")
    ax2.set_ylim(0, 40)
    ax2.legend(ncol=2, fontsize=9)
    fig.tight_layout()
    save(fig, "fig2_sentence_count.png")


def fig3_position_function(agg: dict) -> None:
    cond = agg["position_function"]["conditional"]
    funcs = ["what", "how", "findings", "why_it_matters"]
    short = {"what": "W 研究内容", "how": "H 方法", "findings": "F 结论", "why_it_matters": "Y 意义"}
    titles = {"4": "4 句摘要（n=806）", "5": "5 句摘要（n=1111）", "6": "6 句摘要（n=867）"}
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    for idx, (ax, k) in enumerate(zip(axes, ["4", "5", "6"])):
        mat = np.array([[row["pct_with_function"][f] for row in cond[k]["position_matrix"]]
                        for f in funcs])
        im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(int(k)), [f"第{i+1}句" for i in range(int(k))])
        if idx == 0:
            ax.set_yticks(range(4), [short[f] for f in funcs])
        else:
            ax.set_yticks(range(4), [])
        for i in range(4):
            for jj in range(int(k)):
                v = mat[i, jj]
                ax.text(jj, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if v > 55 else "#1a1a1a")
        ax.set_title(titles[k], fontsize=10)
    fig.colorbar(im, ax=axes, shrink=0.8, label="占比 %")
    save(fig, "fig3_position_function.png")


def fig4_transition_matrix(agg: dict) -> None:
    col = agg["transitions"]["collapsed"]
    rows, cols = col["from_states"], col["to_states"]
    mat = np.array([[col["row_pct"][a][b] for b in cols] for a in rows], dtype=float)
    row_labels = ["开头 START"] + [FUNC_LABEL[s] for s in rows[1:]]
    col_labels = [FUNC_LABEL.get(s, s) for s in cols[:-1]] + ["结尾 END"]
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=100)
    ax.set_xticks(range(len(cols)), col_labels, rotation=25, ha="right")
    ax.set_yticks(range(len(rows)), row_labels)
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = mat[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=9,
                    color="white" if v > 55 else "#1a1a1a")
    ax.set_xlabel("下一句功能")
    ax.set_ylabel("当前句功能")
    fig.colorbar(im, ax=ax, shrink=0.8, label="P(下一句 | 当前句) %")
    save(fig, "fig4_transition_matrix.png")


def fig5_function_coverage(agg: dict) -> None:
    p = agg["function_coverage"]["presence_pct"]
    labels = ["Findings 结论", "How 方法", "What 研究内容", "Why 意义"]
    keys = ["findings", "how", "what", "why_it_matters"]
    vals = [p[k] for k in keys]
    colors = ["#54A24B", "#F58518", "#4C78A8", "#E45756"]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(labels, vals, color=colors, height=0.55)
    for b, v in zip(bars, vals):
        ax.text(v + 1.5, b.get_y() + b.get_height() / 2, f"{v:.1f}%", va="center", fontsize=11)
    ax.set_xlim(0, 110)
    ax.set_xlabel("包含该功能的摘要占比")
    save(fig, "fig5_function_coverage.png")


def fig6_first_last(agg: dict) -> None:
    ep = agg["endpoints"]
    cats = ["W", "H", "F", "Y", "O"]
    dists = {}
    for name, key in [("首句", "first_sentence"), ("末句", "last_sentence")]:
        d = {e["set"]: e["pct"] for e in ep[key]["label_set_distribution"]}
        row = {c: 0.0 for c in cats}
        for s, pct in d.items():
            if s in ("-", "C"):
                row["O"] += pct
            elif len(s) == 1:
                row[s] += pct
            else:  # 多标签句按 F>H>W>Y 坍缩，与转移矩阵口径一致
                for c in ["F", "H", "W", "Y"]:
                    if c in s:
                        row[c] += pct
                        break
        dists[name] = row
    fig, ax = plt.subplots(figsize=(7, 3.4))
    left = np.zeros(2)
    y_pos = [1, 0]
    for c in cats:
        vals = np.array([dists["首句"][c], dists["末句"][c]])
        ax.barh(y_pos, vals, left=left, color=COLORS[c], height=0.5, label=FUNC_LABEL[c])
        for yi, v, l in zip(y_pos, vals, left):
            if v >= 4:
                ax.text(l + v / 2, yi, f"{v:.0f}%", ha="center", va="center", fontsize=9,
                        color="white")
        left += vals
    ax.set_yticks(y_pos, ["首句", "末句"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("占比 %（多标签句按 F>H>W>Y 坍缩）")
    ax.legend(ncol=3, fontsize=8, loc="center", bbox_to_anchor=(0.5, 0.52))
    save(fig, "fig6_first_last.png")


def main() -> None:
    agg = json.load(open(AGG_PATH, encoding="utf-8"))
    fig1_length_by_journal(agg)
    fig1_variants(agg)
    fig2_sentence_count(agg)
    fig3_position_function(agg)
    fig4_transition_matrix(agg)
    fig5_function_coverage(agg)
    fig6_first_last(agg)


if __name__ == "__main__":
    main()
