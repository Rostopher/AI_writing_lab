"""生成博客正文的五张经济学风格图：篇幅、句数、位置、转移、期刊长度。

python modules/academic_research/abstract_structure/plot_abstract_blog_figures.py
使用已有聚合表与公开派生词数，输出路径可由 --out 指定。
图片仅保留统计图、坐标与图例；图题、Notes 和来源放在博客 Markdown 中。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np

import plot_tweet_style_gallery as design


def save_plot(fig, name, directory):
    """移除共用模板的页眉页脚，按图表实际边界导出 PNG 与 SVG。"""
    # 共用模板的 Figure 级文字、装饰线属于说明区；Axes 中的分面标签、
    # 样本量、坐标、图例和色条均保留。
    for text in list(fig.texts):
        text.remove()
    for artist in list(fig.artists):
        artist.remove()
    directory.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        fig.savefig(directory/f"{name}.{extension}", dpi=300,
                    bbox_inches="tight", pad_inches=.08)
    plt.close(fig)


def text_share_figure(agg, theme):
    shares = agg["text_share_pct"]
    codes = ["F", "H", "W", "Y"]
    keys = ["findings", "how", "what", "why_it_matters"]
    fig = plt.figure(figsize=(12, 7.4))
    ax = design.axis(fig, [.245, .235, .65, .47], theme, grid="x")
    for idx, (key, code) in enumerate(zip(keys, codes)):
        value = shares[key]
        fill = theme.palette[design.CATS.index(code)]
        ax.barh(idx, value, height=.46, color=fill, edgecolor=theme.ink, linewidth=.6)
        ax.text(value+1, idx, f"{value:.1f}%", va="center", fontsize=15,
                fontweight="bold" if code == "F" else "normal")
    ax.set_yticks(range(4), [design.LABELS[code] for code in codes], color=theme.ink)
    ax.set_ylim(3.65, -.65)
    ax.set_xlim(0, 58)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.set_xlabel("占摘要篇幅的比例（逐篇平均）")
    return fig


def position_mobile_figure(agg, theme):
    """同一位置矩阵纵向分面，适合公众号与手机正文。"""
    fig = plt.figure(figsize=(8, 12))
    for idx, (k, bottom) in enumerate(zip(["4", "5", "6"], [.65, .405, .16])):
        block = agg["position_function"]["conditional"][k]
        matrix = np.array([[row["pct_with_function"][f] for row in block["position_matrix"]]
                           for f in design.FUNCTIONS])
        ax = fig.add_axes([.23, bottom, .70, .18])
        im = design.heatmap(ax, matrix, theme, size=16)
        ax.set_xticks(np.arange(int(k))+.5, [f"第{i+1}句" for i in range(int(k))], fontsize=13)
        ax.set_yticks(np.arange(4)+.5, ["W 研究内容", "H 方法", "F 结论", "Y 意义"], fontsize=13)
        ax.set_title(f"{chr(97+idx)}   {k} 句摘要", loc="left", fontsize=15, pad=15)
        ax.text(1, 1.095, f"n = {block['n_articles']:,}", transform=ax.transAxes,
                ha="right", fontsize=12, color=theme.muted)
    design.colorbar(fig, im, [.45, .070, .38, .010], "占比 %", theme, horizontal=True)
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure-data", type=Path, default=design.OUTPUT/"figure_data.json")
    parser.add_argument("--out", type=Path, default=design.ROOT/"manuscripts/figures/abstract_structure_blog")
    args = parser.parse_args()
    source = json.loads(args.figure_data.resolve().read_text(encoding="utf-8"))
    agg = source["aggregates"]
    theme = next(t for t in design.THEMES if t.key == "economics")
    with plt.rc_context(design.rc(theme)):
        save_plot(text_share_figure(agg, theme), "fig1_text_share", args.out.resolve())
        fig, _ = design.sentence_figure(agg, theme)
        save_plot(fig, "fig2_sentence_count", args.out.resolve())
        fig, _ = design.position_figure(agg, theme)
        save_plot(fig, "fig3_position_function", args.out.resolve())
        save_plot(position_mobile_figure(agg, theme), "fig3_position_function_mobile", args.out.resolve())
        fig, _ = design.transition_figure(agg, theme)
        save_plot(fig, "fig4_transition_matrix", args.out.resolve())
        fig, _ = design.length_figure(agg, source["word_values_by_journal"], theme, "box")
        for text in fig.axes[0].texts:
            if text.get_text().startswith("p95 "):
                x, y = text.get_position()
                text.set_position((x+.20, y))
                text.set_horizontalalignment("left")
        save_plot(fig, "fig6_length_by_journal", args.out.resolve())
    print(f"5 figures + 1 mobile variant, PNG and SVG: {args.out.resolve()}")


if __name__ == "__main__":
    main()
