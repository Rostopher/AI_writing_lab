"""按功能分组的摘要用词统计：输出审查用表格与经济学风格分组条形图。

python modules/academic_research/abstract_structure/word_frequency_by_function.py
口径：句子按标注功能归入 what/how/findings/why_it_matters（一句可进多组），
统计"含该词的句子占比"而非原始词频；年份不计入数字判断。
产物：Markdown 审查表 + fig6_word_frequency.png/svg。
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np

import plot_tweet_style_gallery as design

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT/"data/processed/abstract_structure"

STOP = set("""the a an and or of to in for on with by from as at is are was were be been
being it its this that these those their his her he she they them which who whom whose not no
do does did done have has had having can could may might will would shall should must
than then so such more most other others any all each both few own same only very just also
into over under between about across after before during within without through per via
how what when where which why if whether while whereas because although though since until
we our i my me us you your one two new used using use based""".split())
YEAR = re.compile(r"\b(19|20)\d{2}\b")
WORD = re.compile(r"[a-z][a-z\-']+")

FUNCTIONS = ["what", "how", "findings", "why_it_matters"]
FUNC_NAMES = {"what": "W 研究内容", "how": "H 方法",
              "findings": "F 结论", "why_it_matters": "Y 意义"}

# 标记词的词形合并：动词用 spaCy lemma（show/showed/shown、find/found、increase/increased
# 等归并），比较级与功能词保留原形（higher/lower 被 lemmatizer 打回 high/low 会丢失方向信息）。
MECH_LEMMAS = {"mechanism", "channel", "explain", "drive"}
MECH_PHRASES = ["driven by", "consistent with", "due to", "account for", "accounts for",
                "through", "because"]
MARKERS = {  # name -> ("lemma", 集合) 或 ("raw", 词/短语列表)
    "we find": ("phrase", ["we find"]),
    "we show": ("phrase", ["we show"]),
    "increase*": ("lemma", {"increase"}),
    "decrease*/reduce*": ("lemma", {"decrease", "reduce", "decline", "fall", "drop"}),
    "机制簇": ("mech", None),
    "welfare": ("raw", ["welfare"]),
    "finally": ("raw", ["finally"]),
    "suggest*": ("lemma", {"suggest"}),
    "first": ("raw", ["first"]),
    "percent*": ("raw", ["percent", "percentage"]),
}


def collect(corpus_path: Path, ann_path: Path):
    corpus = {}
    with corpus_path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                corpus[row["article_id"]] = row
    words = {f: Counter() for f in FUNCTIONS}      # 词 -> 含该词的句子数
    bigrams = {f: Counter() for f in FUNCTIONS}
    n_sents = Counter()
    order_words = defaultdict(Counter)             # F1/F2/... -> 词频（纯发现句）
    order_bigrams = defaultdict(Counter)
    order_n = Counter()
    order_texts = defaultdict(list)                # F1/F2/... -> 原句（供 spaCy 词元分析）
    with ann_path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            ann = json.loads(line)
            doc = corpus.get(ann["article_id"])
            if not doc or not doc.get("sentences"):
                continue
            texts = [s["text"] for s in doc["sentences"]]
            sents = ann["output"]["sentence_annotations"]
            if len(texts) != len(sents):
                continue
            f_order = 0
            for s, text in zip(sents, texts):
                labels = {f["label"] for f in s["functions"]}
                toks = [w for w in WORD.findall(YEAR.sub(" ", text.lower()))
                        if w not in STOP and len(w) > 2]
                if labels == {"findings"}:         # 纯发现句，排除 how+findings 等混合
                    f_order += 1
                    key = f"F{f_order}" if f_order < 4 else "F4+"
                    order_n[key] += 1
                    order_words[key].update(set(toks))
                    order_bigrams[key].update(set(zip(toks, toks[1:])))
                    order_texts[key].append(YEAR.sub(" ", text.lower()))
                for lab in labels:
                    if lab not in words:
                        continue
                    n_sents[lab] += 1
                    words[lab].update(set(toks))       # 每句每词计一次
                    bigrams[lab].update(set(zip(toks, toks[1:])))
    return words, bigrams, n_sents, order_words, order_bigrams, order_n, order_texts


ORDER_KEYS = ["F1", "F2", "F3", "F4+"]


def marker_shares(order_texts, order_n):
    """各标记在 F1/F2/F3/F4+ 的句占比（%）。动词走 spaCy lemma，功能词保留原形。"""
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    shares = {name: [] for name in MARKERS}
    for key in ORDER_KEYS:
        texts = order_texts[key]
        counts = Counter()
        for d in nlp.pipe(texts, batch_size=500):
            lemmas = {t.lemma_ for t in d}
            raw = d.text
            for name, (kind, pat) in MARKERS.items():
                if kind == "lemma" and lemmas & pat:
                    counts[name] += 1
                elif kind == "phrase" and any(p in raw for p in pat):
                    counts[name] += 1
                elif kind == "raw" and any(re.search(rf"\b{re.escape(p)}\b", raw) for p in pat):
                    counts[name] += 1
                elif kind == "mech" and (lemmas & MECH_LEMMAS or any(p in raw for p in MECH_PHRASES)):
                    counts[name] += 1
        for name in MARKERS:
            shares[name].append(counts[name]/order_n[key]*100)
    return shares


def write_table(words, bigrams, n_sents, path: Path, top=30):
    lines = ["# 摘要四功能用词统计（审查表）", "",
             "口径：4250 篇 Top5 摘要（2015—2026），按 v0.3 标注功能分组，一句可进多组；",
             "数值 = 含该词（词组）的句子占该功能句子总数的比例 %。已去停用词与年份。", ""]
    for f in FUNCTIONS:
        n = n_sents[f]
        lines.append(f"## {FUNC_NAMES[f]}（{n} 句）")
        lines.append("")
        lines.append("| 排名 | 词 | 句占比% | 句数 |")
        lines.append("|---|---|---|---|")
        for rank, (w, c) in enumerate(words[f].most_common(top), 1):
            lines.append(f"| {rank} | {w} | {c/n*100:.1f} | {c} |")
        lines.append("")
        lines.append("常见二元组：" +
                     "、".join(f"{' '.join(g)}（{c/n*100:.1f}%）"
                               for g, c in bigrams[f].most_common(12)))
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


ORDER_NAMES = {"F1": "F1 第1句发现", "F2": "F2 第2句发现",
               "F3": "F3 第3句发现", "F4+": "F4+ 第4句及以后"}


def write_order_table(order_words, order_bigrams, order_n, shares, path: Path, top=25):
    lines = ["# 纯发现句用词：按“第几句发现”拆分（审查表）", "",
             "口径：仅含功能标签为纯 findings 的句子（排除 how+findings 等混合句），",
             "按该句在所属摘要中的发现序号分为 F1/F2/F3/F4+（第4句及以后合并）；",
             "数值 = 含该词（词组）的句子占该组句子总数的比例 %。已去停用词与年份。",
             "标记词（下表）动词按 spaCy lemma 归并，比较级与功能词保留原形。", "",
             "## 标记词梯度（图5 数据）", "",
             "| 标记 | F1 | F2 | F3 | F4+ |", "|---|---|---|---|---|"]
    for name, vals in shares.items():
        lines.append(f"| {name} | " + " | ".join(f"{v:.1f}" for v in vals) + " |")
    lines.append("")
    for key in ["F1", "F2", "F3", "F4+"]:
        n = order_n[key]
        lines.append(f"## {ORDER_NAMES[key]}（{n} 句）")
        lines.append("")
        lines.append("| 排名 | 词 | 句占比% | 句数 |")
        lines.append("|---|---|---|---|")
        for rank, (w, c) in enumerate(order_words[key].most_common(top), 1):
            lines.append(f"| {rank} | {w} | {c/n*100:.1f} | {c} |")
        lines.append("")
        lines.append("常见二元组：" +
                     "、".join(f"{' '.join(g)}（{c/n*100:.1f}%）"
                               for g, c in order_bigrams[key].most_common(10)))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def figure(words, n_sents, theme, top=12):
    fig = plt.figure(figsize=(12, 9))
    rects = [[.10, .575, .37, .32], [.565, .575, .37, .32],
             [.10, .115, .37, .32], [.565, .115, .37, .32]]
    for idx, (f, rect) in enumerate(zip(FUNCTIONS, rects)):
        n = n_sents[f]
        items = words[f].most_common(top)
        labels = [w for w, _ in items][::-1]
        vals = np.array([c/n*100 for _, c in items])[::-1]
        ax = design.axis(fig, rect, theme, grid="x")
        color = theme.palette[design.CATS.index({"what": "W", "how": "H",
                                                 "findings": "F", "why_it_matters": "Y"}[f])]
        ax.barh(np.arange(top), vals, height=.55, color=color,
                edgecolor=theme.ink, linewidth=.5)
        for i, (v, (_, c)) in enumerate(zip(vals, items[::-1])):
            ax.text(v+.4, i, f"{v:.0f}%", va="center", fontsize=10, color=theme.ink)
        ax.set_yticks(np.arange(top), labels, color=theme.ink, fontsize=11)
        ax.set_xlim(0, max(vals)*1.22)
        ax.xaxis.set_major_formatter(lambda x, pos: f"{x:.0f}%")
        ax.set_title(f"{FUNC_NAMES[f]}（{n:,} 句）", loc="left",
                     fontsize=13, pad=10, color=theme.ink)
        if idx >= 2:
            ax.set_xlabel("含该词的句子占比")
    return fig


ORDER_PANELS = [
    ("a   宣告退场", ["we find", "we show"]),
    ("b   方向常在，机制居中", ["increase*", "decrease*/reduce*", "机制簇"]),
    ("c   收束进场", ["welfare", "finally", "suggest*"]),
]


def order_figure(shares, order_n, theme):
    """纯发现句的标记词随发现序号的梯度：宣告下行，方向平稳，机制居中，收束上行。"""
    fig = plt.figure(figsize=(14, 5.4))
    line_styles = ["-", "--", "-.", ":"]
    markers = ["o", "s", "^", "D"]
    legend_locs = ["upper right", "lower right", "upper left"]
    for idx, (title, kws) in enumerate(ORDER_PANELS):
        ax = design.axis(fig, [.065+idx*.325, .20, .26, .62], theme, grid="y")
        for j, kw in enumerate(kws):
            ax.plot(range(4), shares[kw], color=theme.ink, lw=1.6, ms=5,
                    linestyle=line_styles[j], marker=markers[j],
                    markeredgewidth=.7, markeredgecolor=theme.bg, label=kw)
        ax.set_xticks(range(4), ORDER_KEYS, color=theme.ink)
        ax.set_ylim(0, None)
        ax.set_title(title, loc="left", fontsize=13, pad=12, color=theme.ink)
        ax.legend(loc=legend_locs[idx], fontsize=11)
        ax.yaxis.set_major_formatter(lambda x, pos: f"{x:.0f}%")
        ax.set_xlabel("摘要中的第几句发现（纯发现句）")
        if idx == 0:
            ax.set_ylabel("含该标记的句子占比")
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path,
                        default=DATA/"run_20260908_a/corpus_manifest.jsonl")
    parser.add_argument("--annotations", type=Path,
                        default=DATA/"run_20260909_v03_full/annotation_flash/annotations.jsonl")
    parser.add_argument("--out", type=Path,
                        default=ROOT/"manuscripts/figures/abstract_structure_blog")
    args = parser.parse_args()
    words, bigrams, n_sents, order_words, order_bigrams, order_n, order_texts = collect(
        args.corpus.resolve(), args.annotations.resolve())
    shares = marker_shares(order_texts, order_n)
    write_table(words, bigrams, n_sents, args.out.resolve()/"word_frequency_by_function.md")
    write_order_table(order_words, order_bigrams, order_n, shares,
                      args.out.resolve()/"word_frequency_findings_by_order.md")
    theme = next(t for t in design.THEMES if t.key == "economics")
    with plt.rc_context(design.rc(theme)):
        fig = figure(words, n_sents, theme)
        for ext in ("png", "svg"):
            fig.savefig(args.out.resolve()/f"word_frequency_panels.{ext}",
                        dpi=300, bbox_inches="tight", pad_inches=.08)
        plt.close(fig)
        fig = order_figure(shares, order_n, theme)
        for ext in ("png", "svg"):
            fig.savefig(args.out.resolve()/f"fig5_findings_order.{ext}",
                        dpi=300, bbox_inches="tight", pad_inches=.08)
        plt.close(fig)
    print(f"tables + panels + fig5: {args.out.resolve()}")


if __name__ == "__main__":
    main()
