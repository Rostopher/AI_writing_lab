"""为摘要结构博客生成五套可复现的图表风格和本地比较页。

用法：python modules/academic_research/abstract_structure/plot_tweet_style_gallery.py
依赖：matplotlib >= 3.9、numpy、Pillow。没有模型调用或数据重标注。
原版 plot_tweet_figures.py 与原版 PNG 保留；仅输出到 styles/。
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import MultipleLocator, PercentFormatter
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/processed/abstract_structure"
OUTPUT = ROOT / "manuscripts/figures/abstract_structure_tweet/styles"
JOURNALS = ["AER", "JPE", "ECMA", "REStud", "QJE"]
FUNCTIONS = ["what", "how", "findings", "why_it_matters"]
CATS = ["W", "H", "F", "Y", "O"]
LABELS = {"W": "What 研究内容", "H": "How 方法", "F": "Findings 结论",
          "Y": "Why 意义", "O": "背景/其他"}
FIGURES = [
    ("fig1_length_by_journal", "01", "不同期刊，摘要有多长？"),
    ("fig1b_violin", "01b", "摘要词数的分布形状"),
    ("fig1c_box", "01c", "摘要词数的分位区间"),
    ("fig2_sentence_count", "02", "一篇摘要通常有几句？"),
    ("fig3_position_function", "03", "每句话分别承担什么功能？"),
    ("fig4_transition_matrix", "04", "一句之后，接什么？"),
    ("fig5_function_coverage", "05", "四类功能有多常见？"),
    ("fig6_first_last", "06", "首句与末句各在做什么？"),
]


@dataclass(frozen=True)
class Theme:
    key: str
    name: str
    descriptor: str
    bg: str
    ink: str
    muted: str
    grid: str
    primary: str
    accent: str
    palette: tuple[str, ...]  # W/H/F/Y/O，在同一套图内固定
    heat: tuple[str, ...]
    body: tuple[str, ...]
    heading: tuple[str, ...]
    size: float
    title_size: float


THEMES = [
    Theme("nature", "Nature", "简洁科学图 · 细线 · 冷色 · 紧凑分面",
          "#FFFFFF", "#20292D", "#6B767A", "#E5E9EB", "#347C91", "#C45B43",
          ("#347C91", "#D59B48", "#417663", "#8E709D", "#A3ADB2"),
          ("#F3F7F8", "#B5D5DF", "#4B90AA", "#164D66"),
          ("Arial", "Microsoft YaHei"), ("Arial", "Microsoft YaHei"), 11, 21),
    Theme("science", "Science", "科学杂志编辑感 · 衬线标题 · 朱红重点",
          "#FFFFFF", "#24282B", "#757779", "#E7E7E7", "#4D657B", "#B73137",
          ("#4D657B", "#B98C49", "#3B7773", "#B73137", "#A8A9A9"),
          ("#F7F5F4", "#CFDFE3", "#668F9F", "#224E65"),
          ("Arial", "Microsoft YaHei"), ("Georgia", "SimSun"), 11.5, 24),
    Theme("economics", "经济学顶刊", "论文排版 · 黑白灰 · 衬线字 · 线型区分",
          "#FFFFFF", "#181818", "#656565", "#DEDEDE", "#555555", "#171717",
          ("#404040", "#AAAAAA", "#6B6B6B", "#DEDEDE", "#F0F0F0"),
          ("#FFFFFF", "#D4D4D4", "#838383", "#252525"),
          ("Times New Roman", "SimSun"), ("Times New Roman", "SimSun"), 12, 22),
    Theme("mckinsey", "麦肯锡", "结论先行 · 深蓝 · 大数字 · 边栏解读",
          "#FFFFFF", "#09233D", "#637181", "#DCE3EA", "#275B94", "#007FAB",
          ("#275B94", "#7EABCB", "#082F55", "#008DAB", "#BAC7D1"),
          ("#F1F5F9", "#B9D8ED", "#3F8FCA", "#082F55"),
          ("Arial", "Microsoft YaHei"), ("Arial", "Microsoft YaHei"), 11.5, 24),
    Theme("substack", "Substack", "暖纸色 · 墨绿与橙 · 衬线标题 · 阅读感",
          "#FAF7EF", "#233D36", "#788079", "#DDDCD2", "#38715E", "#C5653D",
          ("#467B6B", "#D5A24F", "#244D41", "#C5653D", "#B6B9AB"),
          ("#F4F1E7", "#C9DBCA", "#719D88", "#244D41"),
          ("Georgia", "Microsoft YaHei"), ("Georgia", "SimSun"), 11.5, 25),
]


def rc(theme: Theme) -> dict:
    return {
        "font.family": list(theme.body), "font.size": theme.size,
        "axes.labelsize": theme.size, "axes.labelcolor": theme.ink,
        "axes.labelpad": 12, "axes.edgecolor": theme.muted, "axes.linewidth": .7,
        "text.color": theme.ink, "xtick.color": theme.muted, "ytick.color": theme.muted,
        "xtick.labelsize": theme.size, "ytick.labelsize": theme.size,
        "figure.facecolor": theme.bg, "axes.facecolor": theme.bg,
        "savefig.facecolor": theme.bg, "axes.unicode_minus": False,
        "legend.frameon": False, "legend.fontsize": theme.size - 1,
        "svg.fonttype": "none", "pdf.fonttype": 42,
        "hatch.linewidth": .45, "lines.solid_capstyle": "round",
    }


def line(fig, x1, x2, y, color, lw=1):
    fig.add_artist(Line2D([x1, x2], [y, y], transform=fig.transFigure,
                         color=color, linewidth=lw, solid_capstyle="butt"))


def canvas(t: Theme, number: str, title: str, insight: str, note: str, *, wide=False):
    fig = plt.figure(figsize=(15 if wide else 12, 7.4))
    head = dict(fontfamily=list(t.heading), color=t.ink)
    if t.key == "economics":
        fig.text(.5, .931, f"图 {number}   {title}", ha="center", va="top",
                 fontsize=t.title_size, **head)
        fig.text(.5, .865, insight, ha="center", va="top", fontsize=11, color=t.muted)
        line(fig, .08, .94, .816, t.ink, .7)
    elif t.key == "mckinsey":
        line(fig, .065, .935, .954, t.ink, 3)
        fig.text(.065, .918, f"摘要研究  /  TOP FIVE ECONOMICS  /  {number}",
                 fontsize=10, color=t.muted)
        fig.text(.065, .853, insight, fontsize=t.title_size, fontweight="bold", **head)
        fig.text(.065, .798, title, fontsize=11, color=t.muted)
    elif t.key == "substack":
        fig.text(.065, .925, f"THE ABSTRACT NOTEBOOK    /    {number}",
                 fontsize=10, color=t.accent, fontweight="bold")
        fig.text(.065, .851, title, fontsize=t.title_size, **head)
        fig.text(.065, .795, insight, fontsize=12, color=t.muted)
    elif t.key == "science":
        line(fig, .065, .112, .931, t.accent, 4)
        fig.text(.126, .924, f"RESEARCH IN GRAPHICS    /    {number}",
                 fontsize=9.5, color=t.accent, fontweight="bold")
        fig.text(.065, .854, title, fontsize=t.title_size, **head)
        fig.text(.065, .796, insight, fontsize=11.5, color=t.muted)
    else:
        fig.text(.065, .925, f"ABSTRACT STRUCTURE    |    {number}",
                 fontsize=9, color=t.primary, fontweight="bold")
        fig.text(.065, .858, title, fontsize=t.title_size, fontweight="bold", **head)
        fig.text(.065, .803, insight, fontsize=11, color=t.muted)
    line(fig, .065, .935, .118, t.grid, .8)
    fig.text(.065, .083, note, fontsize=9.2, color=t.muted, va="center")
    fig.text(.065, .040, "AI Writing Lab · Top5 已发表摘要 · 2015–2026 · n=4,250 · 功能标注：Flash / v0.3",
             fontsize=8.5, color=t.muted)
    fig.text(.935, .040, f"{number}  /  ABSTRACT STRUCTURE", ha="right", fontsize=8, color=t.muted)
    return fig


def axis(fig, rect, t: Theme, *, grid="y"):
    ax = fig.add_axes(rect)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_visible(t.key == "economics")
    ax.spines["bottom"].set_color(t.grid if t.key != "economics" else t.ink)
    ax.tick_params(axis="both", length=3 if t.key == "economics" else 0, pad=8)
    ax.set_axisbelow(True)
    if grid and t.key != "economics":
        ax.grid(axis=grid, color=t.grid, linewidth=.7)
    return ax


def readable(fill):
    # 对实际底色计算 WCAG 相对亮度，在白字和深色字中选择对比更强的一种。
    rgb = np.array(to_rgb(fill))
    rgb = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    lum = float(rgb @ [0.2126, .7152, .0722])
    return "#FFFFFF" if lum < .179 else "#172A2B"


def precise(value):
    return f"{value:g}"


def sidebar(fig, t, value, label, detail):
    fig.add_artist(Rectangle((.76, .31), .175, .34, transform=fig.transFigure,
                             facecolor="#EFF5FA", edgecolor="none", zorder=0))
    fig.text(.778, .556, value, fontsize=32, color=t.primary, fontweight="bold")
    fig.text(.778, .494, label, fontsize=12, color=t.ink, fontweight="bold")
    fig.text(.778, .389, detail, fontsize=10.2, color=t.muted, linespacing=1.6)


def length_figure(agg, word_values, t, variant="bar"):
    suffix, number, title = {
        "bar": FIGURES[0], "violin": FIGURES[1], "box": FIGURES[2]
    }[variant]
    by = agg["word_count"]["by_journal"]
    meds = np.array([by[j]["median"] for j in JOURNALS])
    p95 = np.array([by[j]["p95"] for j in JOURNALS])
    note = {
        "bar": "柱高为中位数；短横线为 p95（95% 的摘要词数不超过这一值）。",
        "violin": "轮廓为平滑密度；圆点为中位数，菱形为 p95。纵轴沿用原图 0–320 词，长尾未全部展示。",
        "box": "箱体为第25–75百分位；须为 1.5×IQR 范围；菱形为 p95。离群点沿用原版隐藏。",
    }[variant]
    insight = f"AER / JPE 中位 {precise(meds[0])} 词，QJE 达到 {precise(meds[-1])} 词"
    fig = canvas(t, number, title, insight, note)
    side = t.key == "mckinsey" and variant == "bar"
    ax = axis(fig, [.12, .235, .59 if side else .80, .47], t)
    x = np.arange(5)
    colors = [t.primary] * 5
    if t.key in ("science", "substack"):
        colors[-1] = t.accent
    if variant == "bar":
        bars = ax.bar(x, meds, width=.48, color=colors, zorder=3)
        for b, v, c in zip(bars, meds, colors):
            ax.text(b.get_x() + b.get_width()/2, v/2, precise(v), ha="center", va="center",
                    fontsize=14, color=readable(c), fontweight="bold")
        ax.scatter(x, p95, marker="_", s=500, linewidths=1.8, color=t.accent, zorder=4)
        for xx, v in zip(x, p95):
            ax.text(xx, v+8, precise(v), ha="center", va="bottom", fontsize=10.5, color=t.accent)
        ax.set_ylim(0, 275)
        handles = [Patch(facecolor=t.primary, label="中位数"),
                   Line2D([], [], marker="_", markersize=15, color=t.accent, lw=0, label="p95")]
        if side:
            sidebar(fig, t, f"{meds[-1]/meds[0]:.1f}×", "QJE / AER 中位词数", "目标期刊不同\n摘要长度也不同")
    else:
        vals = [word_values[j] for j in JOURNALS]
        if variant == "violin":
            parts = ax.violinplot(vals, positions=x, widths=.70, showextrema=False)
            for body, color in zip(parts["bodies"], colors):
                body.set_facecolor(color)
                body.set_edgecolor(color)
                body.set_alpha(.27 if t.key != "economics" else .18)
                body.set_linewidth(1)
            for xx, j in zip(x, JOURNALS):
                ax.vlines(xx, by[j]["p25"], by[j]["p75"], color=t.primary, lw=3, zorder=3)
            ax.scatter(x, meds, s=26, color=t.ink, edgecolors=t.bg, linewidths=.7, zorder=4)
        else:
            bp = ax.boxplot(vals, positions=x, widths=.45, showfliers=False, patch_artist=True,
                            medianprops=dict(color=t.ink, linewidth=1.7),
                            boxprops=dict(edgecolor=t.primary, linewidth=1),
                            whiskerprops=dict(color=t.primary, linewidth=1),
                            capprops=dict(color=t.primary, linewidth=1))
            for b, c in zip(bp["boxes"], colors):
                b.set_facecolor(c)
                b.set_alpha(.22)
        ax.scatter(x, p95, marker="D", s=28, facecolors=t.bg, edgecolors=t.accent, linewidths=1.4, zorder=4)
        for xx, m, v in zip(x, meds, p95):
            ax.text(xx+.28, m, precise(m), va="center", fontsize=10, color=t.ink)
            ax.text(xx, v+13, f"p95 {precise(v)}", ha="center", fontsize=9, color=t.accent)
        ax.set_ylim(0, 320)
        handles = [Line2D([], [], marker="o" if variant == "violin" else "_", markersize=5,
                          color=t.ink, lw=0, label="中位数"),
                   Line2D([], [], marker="D", markersize=5, markerfacecolor=t.bg,
                          color=t.accent, lw=0, label="p95")]
    ax.set_xlim(-.6, 4.65)
    ax.set_ylabel("摘要词数")
    ax.set_xticks(x, JOURNALS, color=t.ink)
    ax.yaxis.set_major_locator(MultipleLocator(50))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, 1.12), ncol=2, borderaxespad=0)
    return fig, suffix


def sentence_figure(agg, t):
    ks = [str(k) for k in range(3, 10)]
    overall = np.array([agg["sentence_count"]["overall"]["dist_pct"].get(k, 0) for k in ks])
    share = sum(agg["sentence_count"]["overall"]["dist_pct"][k] for k in ["4", "5", "6"])
    fig = canvas(t, "02", FIGURES[3][2], f"4–6 句占 {share:.1f}%，但五刊的分布不同",
                 "两面板沿用原图展示 3–9 句；比例的分母仍是全部摘要，未对展示区间重新归一化。")
    ax1 = axis(fig, [.105, .24, .32, .46], t)
    ax2 = axis(fig, [.525, .24, .395, .46], t)
    colors = [t.primary if k in ["4", "5", "6"] else t.grid for k in ks]
    bars = ax1.bar(np.arange(7), overall, width=.6, color=colors, zorder=3)
    for b, v in zip(bars, overall):
        ax1.text(b.get_x()+b.get_width()/2, v+.75, f"{v:.0f}%", ha="center", fontsize=10)
    ax1.set_xticks(range(7), ks)
    ax1.set_ylim(0, 30)
    ax1.set_xlabel("摘要句数")
    ax1.set_ylabel("占比")
    ax1.yaxis.set_major_locator(MultipleLocator(10))
    ax1.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax1.set_title("a   总体分布", loc="left", fontsize=12, pad=29, color=t.ink)
    line_styles = ["-", "--", "-.", ":", (0, (5, 1, 1, 1))]
    markers = ["o", "s", "^", "D", "v"]
    # 期刊身份用独立色表与点形；不将功能色表直接映射到期刊。
    journal_colors = ["#486C9B", "#A47148", "#8C72A4", "#4A8783", "#BA5C67"]
    line_ends = []
    for i, journal in enumerate(JOURNALS):
        vals = [agg["sentence_count"]["by_journal"][journal]["dist_pct"].get(k, 0) for k in ks]
        ax2.plot(range(7), vals, label=journal, color=t.ink if t.key == "economics" else journal_colors[i],
                 marker=markers[i], ms=4, lw=1.5 if t.key == "economics" else 1.9,
                 linestyle=line_styles[i] if t.key == "economics" else "-",
                 markeredgewidth=.7, markeredgecolor=t.bg)
        line_ends.append((vals[-1], journal, t.ink if t.key == "economics" else journal_colors[i]))
    ax2.set_xticks(range(7), ks)
    ax2.set_ylim(0, 40)
    ax2.set_xlim(-.25, 8.35)
    ax2.set_xlabel("摘要句数")
    ax2.set_ylabel("占比")
    ax2.yaxis.set_major_locator(MultipleLocator(10))
    ax2.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax2.set_title("b   按期刊", loc="left", fontsize=12, pad=29, color=t.ink)
    for idx, (end, journal, color) in enumerate(sorted(line_ends)):
        label_y = 2.1 + idx*4.5
        ax2.plot([6.12, 6.55, 6.85], [end, label_y, label_y], color=color, lw=.7, alpha=.8)
        ax2.text(6.95, label_y, journal, fontsize=9.5, color=color, va="center")
    return fig, FIGURES[3][0]


def heatmap(ax, matrix, t, *, size=12):
    cmap = LinearSegmentedColormap.from_list(t.key, t.heat)
    im = ax.pcolormesh(matrix, cmap=cmap, vmin=0, vmax=100, shading="flat",
                       edgecolors=t.bg, linewidth=1.5, rasterized=False)
    ax.set_ylim(matrix.shape[0], 0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0, pad=11, labelcolor=t.ink)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            label = "<1" if 0 < value < .5 else f"{value:.0f}"
            ax.text(col+.5, row+.5, label, ha="center", va="center", fontsize=size,
                    color=readable(cmap(value/100)), fontweight="bold" if value >= 50 else "normal")
    return im


def colorbar(fig, im, rect, label, t, *, horizontal=False):
    cax = fig.add_axes(rect)
    cb = fig.colorbar(im, cax=cax, orientation="horizontal" if horizontal else "vertical")
    cb.outline.set_visible(False)
    cb.set_ticks([0, 25, 50, 75, 100])
    cb.ax.tick_params(length=0, labelsize=9, pad=6)
    cb.set_label(label, fontsize=10, labelpad=8, color=t.muted)


def position_figure(agg, t):
    fig = canvas(t, "03", FIGURES[4][2], "研究内容靠前，结论在后半段更常见",
                 "单元格为该位置包含该功能的比例（%）；一句可有多个功能，列和不必为100%。<1 表示非零但不足0.5%。",
                 wide=True)
    panels = [[.13, .30, .195, .38], [.36, .30, .244, .38], [.639, .30, .293, .38]]
    # 相同句子位置使用相同格宽；按 4:5:6 分配面板宽度。
    for idx, (k, rect) in enumerate(zip(["4", "5", "6"], panels)):
        block = agg["position_function"]["conditional"][k]
        matrix = np.array([[row["pct_with_function"][f] for row in block["position_matrix"]] for f in FUNCTIONS])
        ax = fig.add_axes(rect)
        im = heatmap(ax, matrix, t, size=11)
        ax.set_xticks(np.arange(int(k))+.5, [f"第{i+1}句" for i in range(int(k))], fontsize=10)
        ax.set_yticks(np.arange(4)+.5, ["W 研究内容", "H 方法", "F 结论", "Y 意义"] if idx == 0 else [])
        ax.set_title(f"{chr(97+idx)}   {k} 句摘要", loc="left", fontsize=13, pad=30, fontweight="bold")
        ax.text(0, 1.055, f"n = {block['n_articles']:,}", transform=ax.transAxes,
                fontsize=10, color=t.muted)
    colorbar(fig, im, [.43, .205, .25, .016], "占比 %", t, horizontal=True)
    return fig, FIGURES[4][0]


def transition_figure(agg, t):
    block = agg["transitions"]["collapsed"]
    rows, cols = block["from_states"], block["to_states"]
    matrix = np.array([[block["row_pct"][a][b] for b in cols] for a in rows])
    fig = canvas(t, "04", FIGURES[5][2], "方法之后多接结论，意义之后常结束摘要",
                 "按行计算条件概率；多标签句按 F>H>W>Y 坍缩。数值为百分比，四舍五入后行和可能略偏离100。")
    ax = fig.add_axes([.23, .28, .52, .44])
    im = heatmap(ax, matrix, t, size=12)
    xlabels = [LABELS.get(s, "结尾 END").replace(" ", "\n", 1) for s in cols]
    ylabels = ["开头 START" if s == "START" else LABELS[s] for s in rows]
    ax.set_xticks(np.arange(len(cols))+.5, xlabels, fontsize=10)
    ax.set_yticks(np.arange(len(rows))+.5, ylabels, fontsize=11)
    ax.set_xlabel("下一句功能", labelpad=15)
    ax.set_ylabel("当前句功能", labelpad=13)
    colorbar(fig, im, [.80, .31, .015, .36], "P(下一句 | 当前句) %", t)
    if t.key in ("science", "mckinsey", "substack"):
        for a, b in [("H", "F"), ("F", "F"), ("Y", "END")]:
            ax.add_patch(Rectangle((cols.index(b)+.035, rows.index(a)+.035), .93, .93,
                                   fill=False, edgecolor=t.accent, linewidth=1.4))
    return fig, FIGURES[5][0]


def coverage_figure(agg, t):
    p = agg["function_coverage"]["presence_pct"]
    keys, codes = ["findings", "how", "what", "why_it_matters"], ["F", "H", "W", "Y"]
    vals = [p[k] for k in keys]
    fig = canvas(t, "05", FIGURES[6][2], f"{p['findings']:.1f}% 的摘要有结论，{p['why_it_matters']:.1f}% 明说研究意义",
                 "出现率：至少一句包含该功能的摘要占比；What 沿用原图 narrow 口径；一句可包含多个功能。")
    side = t.key == "mckinsey"
    ax = axis(fig, [.235, .235, .47 if side else .68, .47], t, grid="x")
    colors = [t.palette[CATS.index(c)] for c in codes]
    for i, (v, c) in enumerate(zip(vals, colors)):
        if t.key in ("mckinsey", "substack"):
            ax.barh(i, 100, height=.47, color=t.grid, alpha=.33, zorder=1)
        ax.barh(i, v, height=.47, color=c, edgecolor=t.ink if t.key == "economics" else "none",
                linewidth=.65, zorder=3)
        ax.text(v+1.7, i, f"{v:.1f}%", va="center", fontsize=14, color=t.ink,
                fontweight="bold" if t.key != "economics" else "normal")
    ax.set_yticks(range(4), [LABELS[c] for c in codes], color=t.ink)
    ax.set_ylim(-.65, 3.65)  # 沿用原图自下而上的功能顺序
    ax.set_xlim(0, 112)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.set_xlabel("包含该功能的摘要占比")
    if side:
        sidebar(fig, t, f"{p['why_it_matters']:.1f}%", "摘要明说研究意义", "描述已发表样本\n不等于写作必选项")
    return fig, FIGURES[6][0]


def endpoint_values(agg):
    result = []
    for key in ["first_sentence", "last_sentence"]:
        row = dict.fromkeys(CATS, 0.0)
        for entry in agg["endpoints"][key]["label_set_distribution"]:
            s, pct = entry["set"], entry["pct"]
            if s in ("-", "C"):
                row["O"] += pct
            elif len(s) == 1:
                row[s] += pct
            else:
                for code in ["F", "H", "W", "Y"]:
                    if code in s:
                        row[code] += pct
                        break
        result.append(row)
    return result


def endpoint_figure(agg, t):
    rows = endpoint_values(agg)
    fig = canvas(t, "06", FIGURES[7][2], "首句交代问题与方法，末句多报告结论",
                 "多标签句按 F>H>W>Y 坍缩为一种功能；小于4%的分段不标数字。四舍五入可能使总和略偏离100%。")
    ax = axis(fig, [.12, .265, .80, .37], t, grid=None)
    left = np.zeros(2)
    hatches = [None, "///", None, "...", None]
    handles = []
    for idx, c in enumerate(CATS):
        vals = np.array([r[c] for r in rows])
        color = t.palette[idx]
        hatch = hatches[idx] if t.key == "economics" else None
        ax.barh([1, 0], vals, left=left, height=.42, color=color,
                edgecolor=t.ink if hatch else t.bg, linewidth=.65, hatch=hatch)
        for y, v, l in zip([1, 0], vals, left):
            if v >= 4:
                ax.text(l+v/2, y, f"{v:.0f}%", ha="center", va="center", fontsize=12,
                        fontweight="bold" if v >= 20 else "normal", color=readable(color))
        handles.append(Patch(facecolor=color, edgecolor=t.ink if hatch else "none", hatch=hatch, label=LABELS[c]))
        left += vals
    ax.set_yticks([1, 0], ["首句", "末句"], fontsize=13, color=t.ink)
    ax.set_ylim(-.50, 1.50)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("占比 %（多标签句按 F>H>W>Y 坍缩）")
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(.52, .707), ncol=5,
               handlelength=1.1, columnspacing=1.5, handletextpad=.5)
    return fig, FIGURES[7][0]


def load_words(corpus: Path, sample: Path):
    with sample.open(encoding="utf-8") as stream:
        journal_of = {r["article_id"]: r["journal_code"]
                      for line in stream if line.strip() for r in [json.loads(line)]}
    values = {j: [] for j in JOURNALS}
    with corpus.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            journal = journal_of.get(row["article_id"])
            if journal is not None and row["word_count_v1"] is not None:
                values[journal].append(row["word_count_v1"])
    return values


def save_figure(fig, name, directory, dpi):
    directory.mkdir(parents=True, exist_ok=True)
    # 固定画布，不使用 tight 裁剪，保证各风格在比较页的尺寸一致。
    fig.savefig(directory / f"{name}.png", dpi=dpi)
    fig.savefig(directory / f"{name}.svg")
    plt.close(fig)


def contact_sheets(output: Path, themes: list[Theme]):
    font = ImageFont.truetype(findfont(FontProperties(family="Microsoft YaHei")), 24)
    small = ImageFont.truetype(findfont(FontProperties(family="Microsoft YaHei")), 17)
    # 每套八图总览；使用已生成的 PNG 缩略图，不重新绘制统计内容。
    for t in themes:
        sheet = Image.new("RGB", (1600, 2070), t.bg)
        draw = ImageDraw.Draw(sheet)
        draw.text((42, 25), f"{t.name}  /  {t.descriptor}", font=font, fill=t.ink)
        for i, (stem, number, title) in enumerate(FIGURES):
            x, y = 30+(i%2)*790, 92+(i//2)*490
            draw.text((x+6, y), f"{number}  {title}", font=small, fill=t.muted)
            with Image.open(output/t.key/f"{stem}.png") as source:
                thumb = source.convert("RGB")
                thumb.thumbnail((770, 440), Image.Resampling.LANCZOS)
                sheet.paste(thumb, (x+(770-thumb.width)//2, y+33+(440-thumb.height)//2))
        sheet.save(output/t.key/"overview.png")
    # 同一核心热力图的五种版本，最后一个位置给原图作为参照。
    sheet = Image.new("RGB", (1800, 1580), "#ECEFEB")
    draw = ImageDraw.Draw(sheet)
    draw.text((36, 25), "同一组数据，五种视觉表达", font=font, fill="#22372F")
    items = [(t.name, output/t.key/"fig3_position_function.png") for t in themes]
    original = output.parent/"fig3_position_function.png"
    if original.exists():
        items.append(("原版 / 对照", original))
    for i, (name, path) in enumerate(items):
        x, y = 25+(i%2)*890, 90+(i//2)*490
        draw.text((x+10, y), name, font=font, fill="#22372F")
        with Image.open(path) as source:
            thumb = source.convert("RGB")
            thumb.thumbnail((865, 430), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x+(865-thumb.width)//2, y+40+(430-thumb.height)//2))
    sheet.save(output/"style_comparison.png")


def gallery(output: Path, themes: list[Theme]):
    config = {
        "themes": [{"key": t.key, "name": t.name, "description": t.descriptor,
                    "palette": t.palette, "bg": t.bg} for t in themes],
        "figures": [{"stem": stem, "number": num, "title": title} for stem, num, title in FIGURES],
    }
    template = Path(__file__).with_name("tweet_style_gallery.html").read_text(encoding="utf-8")
    (output/"index.html").write_text(template.replace("__GALLERY_CONFIG__", json.dumps(config, ensure_ascii=False)), encoding="utf-8")
    for t in themes:
        rows = "\n".join(f"| {num} | {title} | [{stem}.png]({stem}.png) | [SVG]({stem}.svg) |"
                         for stem, num, title in FIGURES)
        (output/t.key/"README.md").write_text(
            f"# {t.name} 风格\n\n{t.descriptor}。用于博客配图的视觉演绎，不是官方投稿模板。\n\n"
            f"[返回比较页](../index.html) · [本套总览](overview.png) · [数据与生成说明](../README.md)\n\n"
            f"| 编号 | 内容 | PNG | 矢量版 |\n|---|---|---|---|\n{rows}\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aggregates", type=Path, default=DATA/"run_20260909_v03_full/v03_full_tweet_aggregates.json")
    parser.add_argument("--corpus", type=Path, default=DATA/"run_20260908_a/corpus_manifest.jsonl")
    parser.add_argument("--sample", type=Path, default=DATA/"run_20260909_v03_full/full_sample_manifest.jsonl")
    parser.add_argument("--figure-data", type=Path, help="直接使用已导出的 figure_data.json，免读原始台账")
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    if args.figure_data:
        source = json.loads(args.figure_data.resolve().read_text(encoding="utf-8"))
        agg, values = source["aggregates"], source["word_values_by_journal"]
    else:
        agg = json.loads(args.aggregates.resolve().read_text(encoding="utf-8"))
        values = load_words(args.corpus.resolve(), args.sample.resolve())
    args.out.resolve().mkdir(parents=True, exist_ok=True)
    (args.out.resolve()/"figure_data.json").write_text(json.dumps(
        {"aggregates": agg, "word_values_by_journal": values}, ensure_ascii=False, indent=2), encoding="utf-8")
    for t in THEMES:
        for family in set(t.body+t.heading):
            findfont(FontProperties(family=family), fallback_to_default=False)
        with plt.rc_context(rc(t)):
            for variant in ["bar", "violin", "box"]:
                fig, name = length_figure(agg, values, t, variant)
                save_figure(fig, name, args.out.resolve()/t.key, args.dpi)
            for fn in [sentence_figure, position_figure, transition_figure, coverage_figure, endpoint_figure]:
                fig, name = fn(agg, t)
                save_figure(fig, name, args.out.resolve()/t.key, args.dpi)
        print(f"{t.key}: 8 PNG + 8 SVG", flush=True)
    contact_sheets(args.out.resolve(), THEMES)
    gallery(args.out.resolve(), THEMES)
    print(f"Gallery: {args.out.resolve() / 'index.html'}")


if __name__ == "__main__":
    main()
