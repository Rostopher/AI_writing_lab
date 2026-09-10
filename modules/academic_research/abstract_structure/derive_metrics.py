"""派生指标：按设计 §10 从 corpus_manifest + annotations 计算长度、功能、覆盖、
句数、文本占比、顺序、框架外内容等指标。

输入：
- corpus_manifest.jsonl（extract_abstracts 产物）
- 一个或多个 annotations.jsonl：
  * 模型格式（run_annotation 落盘）：{article_id, model, output:{...}, repaired?, cost_cny?}
  * agent 参照格式（build_dev_annotations 落盘）：{article_id, annotator, sentence_annotations, paper_type}
- sample manifest（pilot_sample_manifest.jsonl，含 anon_id）；不给则用全量 included+available+selected

输出：derived_metrics.json + 控制台摘要。

口径要点（设计 §10）：
- 模型失败 = 缺失值（null），明确缺失 = []，二者分开。
- 出现状态三态：present / unclear（仅有对应候选 uncertain 片段）/ absent。
- 覆盖报下界（只计确定满足）与上界（全部 unresolved 计为满足），是识别边界不是置信区间。
- inclusive What = 窄 What ∪ finding_focus=central 的 findings 句；
  finding_focus=unclear 的 findings 句使 inclusive What 记 unresolved，不按 absent 处理。
- 文本占比按 quote 词数占摘要总词数估算（同功能重叠语段合并去重）；
  quote 定位失败率 >5% 时停用占比结论，只保留句子指标。
- 顺序：仅在相关功能明确 present 的子样本比较；'<' 严格、'=' 共现，tie 不当严格顺序；
  块顺序 max(前功能句号) < min(后功能句号)；why 缺失不算违规。
- §10.10 规则矩阵留 TODO（规则审查第二阶段，本轮未运行）。

TODO(§10.10): 规则审查 prompt 运行后在此追加规则矩阵派生。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_abstracts import OUTPUT_ROOT  # noqa: E402
from textnorm import word_count_v1  # noqa: E402

FUNCTIONS = ("what", "how", "findings", "why_it_matters")
CORE3 = ("what", "how", "findings")
QUOTE_FAILURE_DISABLE_THRESHOLD = 0.05

DEFAULT_RUN_DIR = OUTPUT_ROOT / "run_20260908_a"


# ---------------------------------------------------------------------------
# 输入加载
# ---------------------------------------------------------------------------
def load_corpus(path: Path) -> dict[str, dict]:
    corpus: dict[str, dict] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                corpus[rec["article_id"]] = rec
    return corpus


def load_sample(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_annotations(path: Path) -> tuple[str, dict[str, dict], dict]:
    """读一个 annotations 文件。返回 (source_name, {article_id: ann}, file_stats)。

    ann 统一为 {sentence_annotations, paper_type, needs_review}。
    file_stats 记录原始/修复成功数、失败数与费用（模型文件）；agent 文件只有 n_annotated。
    """
    anns: dict[str, dict] = {}
    stats: dict = {"file": str(path), "format": None}
    n_orig = n_rep = 0
    cost = 0.0
    cost_unknown = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if "output" in rec:  # 模型格式
                stats["format"] = "model"
                out = rec["output"]
                ann = {"sentence_annotations": out["sentence_annotations"],
                       "paper_type": out["paper_type"],
                       "needs_review": rec.get("needs_review") or []}
                if rec.get("repaired"):
                    n_rep += 1
                else:
                    n_orig += 1
                if rec.get("cost_cny") is None:
                    cost_unknown += 1
                else:
                    cost += rec["cost_cny"]
                stats.setdefault("model", rec.get("model"))
            else:  # agent 参照格式
                stats["format"] = "agent"
                ann = {"sentence_annotations": rec["sentence_annotations"],
                       "paper_type": rec.get("paper_type"),
                       "needs_review": []}
                stats.setdefault("annotator", rec.get("annotator"))
            anns[rec["article_id"]] = ann
    stats["n_annotated"] = len(anns)
    if stats["format"] is None:
        stats["format"] = "empty"
    if stats["format"] == "agent":
        name = f"agent:{stats.get('annotator') or path.stem}"
    else:
        name = f"model:{stats.get('model') or path.parent.name}"
    return name, anns, stats


# ---------------------------------------------------------------------------
# 基础统计
# ---------------------------------------------------------------------------
def length_stats(values: list[int]) -> dict:
    if not values:
        return {"n": 0}
    s = sorted(values)
    n = len(s)

    def pct(p: float) -> float:
        k = (n - 1) * p
        lo, hi = int(k), min(int(k) + 1, n - 1)
        return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 1)

    return {
        "n": n,
        "mean": round(statistics.mean(s), 1),
        "median": statistics.median(s),
        "p5": pct(0.05), "p25": pct(0.25), "p75": pct(0.75), "p95": pct(0.95),
        "bins": {
            "<100": sum(1 for v in s if v < 100),
            "=100": sum(1 for v in s if v == 100),
            "101-150": sum(1 for v in s if 101 <= v <= 150),
            ">150": sum(1 for v in s if v > 150),
            "<=100": sum(1 for v in s if v <= 100),
        },
    }


def _locate_quote(sentence_text: str, quote: str) -> list[tuple[int, int]]:
    """quote 在句内全部 [start,end) 位置；空 quote 或无匹配返回 []。"""
    if not quote:
        return []
    spans: list[tuple[int, int]] = []
    start = 0
    while True:
        i = sentence_text.find(quote, start)
        if i == -1:
            return spans
        spans.append((i, i + len(quote)))
        start = i + 1


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """合并重叠偏移段（用于同功能 token 去重）。"""
    merged: list[list[int]] = []
    for a, b in sorted(spans):
        if merged and a < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


# ---------------------------------------------------------------------------
# 单篇派生
# ---------------------------------------------------------------------------
def derive_article(ann: dict, rec: dict) -> dict:
    """由一篇标注 + 语料记录派生功能列表、出现状态、覆盖、句数、占比、顺序输入。"""
    sent_text = {s["sentence_id"]: s["text"] for s in rec["sentences"]}
    sent_start = {s["sentence_id"]: s["start"] for s in rec["sentences"]}
    norm_text = rec["abstract_normalized"]
    total_words = rec.get("word_count_v1")

    func_sents: dict[str, set[int]] = {f: set() for f in FUNCTIONS}
    func_gspans: dict[str, list[tuple[int, int]]] = {f: [] for f in FUNCTIONS}
    central_findings: set[int] = set()
    unclear_findings: set[int] = set()
    other_sents: set[int] = set()
    other_gspans: list[tuple[int, int]] = []
    other_descs: list[str] = []
    uncertain_sents: set[int] = set()
    uncertain_candidates: set[str] = set()
    n_quotes = n_quote_fail = n_quote_ambiguous = 0

    def locate_all(sid: int, quote: str) -> list[tuple[int, int]]:
        nonlocal n_quotes, n_quote_fail, n_quote_ambiguous
        n_quotes += 1
        spans = _locate_quote(sent_text.get(sid, ""), quote)
        if not spans:
            n_quote_fail += 1
        elif len(spans) > 1:
            # 同句重复片段位置不唯一：标 needs_review（校验层），占比只取其一
            # （相同子串词贡献相同，不构成任选标签）
            n_quote_ambiguous += 1
        return spans[:1]

    for sa in ann["sentence_annotations"]:
        sid = sa["sentence_id"]
        if sid not in sent_text:
            continue  # 契约校验层已拒绝；防御性跳过
        base = sent_start[sid]
        for fobj in sa.get("functions", []):
            label = fobj.get("label")
            if label not in FUNCTIONS:
                continue
            for ev in fobj.get("evidence", []):
                for a, b in locate_all(sid, ev.get("quote", "")):
                    func_gspans[label].append((base + a, base + b))
                    func_sents[label].add(sid)
                if label == "findings":
                    if ev.get("finding_focus") == "central":
                        central_findings.add(sid)
                    elif ev.get("finding_focus") == "unclear":
                        unclear_findings.add(sid)
        for oc in sa.get("other_content", []):
            other_sents.add(sid)
            if oc.get("function_description"):
                other_descs.append(oc["function_description"])
            for a, b in locate_all(sid, oc.get("quote", "")):
                other_gspans.append((base + a, base + b))
        for uc in sa.get("uncertain_content", []):
            uncertain_sents.add(sid)
            uncertain_candidates.update(
                c for c in uc.get("candidate_functions", []) if c in FUNCTIONS)

    # §10.2 功能列表（去重排序）
    func_lists = {f: sorted(func_sents[f]) for f in FUNCTIONS}

    # inclusive What = 窄 What ∪ central findings 句；unclear findings 句 → unresolved
    what_incl = sorted(func_sents["what"] | central_findings)
    what_incl_unresolved = sorted(unclear_findings - func_sents["what"]
                                  - central_findings)

    # §10.3 出现状态（三态；inclusive What 的 unclear 记 unresolved）
    presence: dict[str, str] = {}
    for f in FUNCTIONS:
        if func_sents[f]:
            presence[f] = "present"
        elif f in uncertain_candidates:
            presence[f] = "unclear"
        else:
            presence[f] = "absent"
    if what_incl:
        presence["what_inclusive"] = "present"
    elif what_incl_unresolved or "what" in uncertain_candidates:
        presence["what_inclusive"] = "unresolved"
    else:
        presence["what_inclusive"] = "absent"

    # §10.4 覆盖：下界只计确定满足；上界把 unclear/unresolved 计为满足
    def coverage(required: tuple[str, ...], what_key: str) -> dict:
        states = [presence[what_key if r == "what" else r] for r in required]
        lower = all(s == "present" for s in states)
        upper = all(s in ("present", "unclear", "unresolved") for s in states)
        return {"lower": lower, "upper": upper, "unresolved": upper and not lower}

    cov = {
        "narrow": {
            "core3": coverage(CORE3, "what"),
            "why": {"lower": presence["why_it_matters"] == "present",
                    "upper": presence["why_it_matters"] in ("present", "unclear"),
                    "unresolved": presence["why_it_matters"] == "unclear"},
            "all4": coverage(FUNCTIONS, "what"),
        },
        "inclusive": {
            "core3": coverage(CORE3, "what_inclusive"),
            "all4": coverage(FUNCTIONS, "what_inclusive"),
        },
    }

    # §10.5 句数与规则（总体分母 + 该功能 present 条件分母在聚合层给出）
    n_sents = {f: len(func_sents[f]) for f in FUNCTIONS}
    n_sents["what_inclusive"] = len(what_incl)
    rules: dict[str, dict] = {}
    for f, ok in (("what", lambda n: 1 <= n <= 2),
                  ("what_inclusive", lambda n: 1 <= n <= 2),
                  ("how", lambda n: n == 1),
                  ("findings", lambda n: n == 1 or n == 2)):
        rules[f] = {
            # 该功能 present 时是否满足句数规则；功能 absent 记 None（聚合层单独给分母）
            "satisfied_if_present": (ok(n_sents[f]) if n_sents[f] > 0 else None),
            "satisfied_overall": ok(n_sents[f]),
        }

    # 只有单个核心功能且无 other/uncertain 的句子数
    n_single_core_clean = 0
    for sa in ann["sentence_annotations"]:
        sid = sa["sentence_id"]
        labels = {f for f in CORE3 if sid in func_sents[f]}
        if len(labels) == 1 and sid not in other_sents and sid not in uncertain_sents:
            n_single_core_clean += 1

    # §10.6 文本占比（quote 词数 / 摘要总词数；同功能重叠合并；另报核心并集）
    text_share: dict = {}
    if total_words:
        for f in FUNCTIONS:
            merged = _merge_spans(func_gspans[f])
            w = sum(word_count_v1(norm_text[a:b])[0] for a, b in merged)
            text_share[f] = round(w / total_words, 4)
        union = _merge_spans([sp for f in FUNCTIONS for sp in func_gspans[f]])
        text_share["core_union"] = round(
            sum(word_count_v1(norm_text[a:b])[0] for a, b in union) / total_words, 4)
        omerged = _merge_spans(other_gspans)
        text_share["other"] = round(
            sum(word_count_v1(norm_text[a:b])[0] for a, b in omerged) / total_words, 4)

    # §10.7 顺序输入：首现句号 + 各功能句列表（块顺序用）
    first = {f: (min(func_sents[f]) if func_sents[f] else None) for f in FUNCTIONS}
    first["what_inclusive"] = min(what_incl) if what_incl else None

    return {
        "function_lists": func_lists,
        "function_lists_what_inclusive": what_incl,
        "what_inclusive_unresolved_sents": what_incl_unresolved,
        "presence": presence,
        "coverage": cov,
        "n_sents": n_sents,
        "rules": rules,
        "n_single_core_clean_sentences": n_single_core_clean,
        "text_share": text_share,
        "first_sentence": first,
        "block": {f: sorted(func_sents[f]) for f in FUNCTIONS},
        "block_what_inclusive": what_incl or None,
        "other_sents": sorted(other_sents),
        "other_descriptions": other_descs,
        "uncertain_sents": sorted(uncertain_sents),
        "has_core_uncertainty": bool(uncertain_candidates & set(FUNCTIONS)),
        "n_quotes": n_quotes,
        "n_quote_fail": n_quote_fail,
        "n_quote_ambiguous": n_quote_ambiguous,
        "primary_type": (ann.get("paper_type") or {}).get("primary_type"),
    }


# ---------------------------------------------------------------------------
# 聚合
# ---------------------------------------------------------------------------
def _cmp(a: int, b: int) -> str:
    return "<" if a < b else ("=" if a == b else ">")


def aggregate_source(derived: dict[str, dict], sample_ids: list[str]) -> dict:
    """语义指标统计范围 = 该来源全部已标注文章；样本内/外分别计数。

    （dev 集与 pilot sample 去重时，开发集标注的指标仍应可算并标注范围。）
    """
    sample_set = set(sample_ids)
    annotated = sorted(derived)
    missing = [a for a in sample_ids if a not in derived]
    arts = [derived[a] for a in annotated]
    n = len(arts)
    n_in_sample = sum(1 for a in annotated if a in sample_set)

    # §10.3 出现状态
    presence_keys = list(FUNCTIONS) + ["what_inclusive"]
    presence = {k: dict(Counter(d["presence"][k] for d in arts)) for k in presence_keys}

    # §10.4 覆盖
    def cov_agg(variant: str, key: str) -> dict:
        lo = sum(1 for d in arts if d["coverage"][variant][key]["lower"])
        hi = sum(1 for d in arts if d["coverage"][variant][key]["upper"])
        return {"lower": lo, "upper": hi, "unresolved": hi - lo, "n": n}

    coverage = {
        "narrow": {k: cov_agg("narrow", k) for k in ("core3", "why", "all4")},
        "inclusive": {k: cov_agg("inclusive", k) for k in ("core3", "all4")},
        "note": "下界只计确定满足；上界把 unclear/unresolved 计为满足。识别边界，非置信区间。",
    }

    # §10.5 句数与规则
    def rule_agg(f: str) -> dict:
        cond = [d for d in arts if d["rules"][f]["satisfied_if_present"] is not None]
        return {
            "satisfied_overall": sum(1 for d in arts if d["rules"][f]["satisfied_overall"]),
            "n_overall": n,
            "satisfied_if_present": sum(
                1 for d in cond if d["rules"][f]["satisfied_if_present"]),
            "n_present": len(cond),
        }

    n_core3_present = sum(
        1 for d in arts if all(d["presence"][f] == "present" for f in CORE3))
    sentence_counts = {
        "distribution": {f: {str(k): v for k, v in sorted(
            Counter(d["n_sents"][f] for d in arts).items())} for f in presence_keys},
        "rules": {f: rule_agg(f)
                  for f in ("what", "what_inclusive", "how", "findings")},
        "joint_what1_2_how1_findings1_2": {
            "satisfied_overall": sum(
                1 for d in arts
                if d["rules"]["what"]["satisfied_overall"]
                and d["rules"]["how"]["satisfied_overall"]
                and d["rules"]["findings"]["satisfied_overall"]),
            "n_overall": n,
            "satisfied_all_present": sum(
                1 for d in arts
                if all(d["presence"][f] == "present" for f in CORE3)
                and d["rules"]["what"]["satisfied_if_present"]
                and d["rules"]["how"]["satisfied_if_present"]
                and d["rules"]["findings"]["satisfied_if_present"]),
            "n_all_present": n_core3_present,
        },
        "n_single_core_clean_sentences": sum(
            d["n_single_core_clean_sentences"] for d in arts),
        "note": "Why 无句数要求；多标签合计可超过总句数。",
    }

    # §10.6 文本占比
    total_quotes = sum(d["n_quotes"] for d in arts)
    fail_quotes = sum(d["n_quote_fail"] for d in arts)
    fail_rate = fail_quotes / total_quotes if total_quotes else 0.0
    shares = [d for d in arts if d["text_share"]]
    text_share: dict = {
        "quote_location": {
            "n_quotes": total_quotes, "n_failed": fail_quotes,
            "failure_rate": round(fail_rate, 4),
            "n_ambiguous_same_sentence": sum(d["n_quote_ambiguous"] for d in arts)},
    }
    if fail_rate > QUOTE_FAILURE_DISABLE_THRESHOLD:
        text_share["disabled"] = True
        text_share["note"] = (f"quote 定位失败率 {fail_rate:.1%} > 5%，按设计停用占比结论，"
                              "只保留句子指标。")
    else:
        text_share["disabled"] = False
        text_share["mean_share"] = (
            {k: round(statistics.mean(d["text_share"][k] for d in shares), 4)
             for k in list(FUNCTIONS) + ["core_union", "other"]} if shares else {})
        text_share["note"] = "quote 词数占摘要总词数的近似占比；同功能重叠语段已合并去重。"

    # §10.7 顺序（narrow/inclusive 两套；仅在相关功能明确 present 的子样本）
    def order_block(what_key: str) -> dict:
        pairs: dict[str, dict] = {}
        for fa, fb in (("what", "how"), ("how", "findings"), ("what", "findings")):
            ka = what_key if fa == "what" else fa
            c: Counter = Counter()
            for d in arts:
                a, b = d["first_sentence"][ka], d["first_sentence"][fb]
                if a is not None and b is not None:
                    c[_cmp(a, b)] += 1
            pairs[f"{ka}~{fb}"] = dict(c)

        def blocks(d: dict):
            wa = (d["block_what_inclusive"] if what_key == "what_inclusive"
                  else d["block"]["what"])
            return wa or None, d["block"]["how"] or None, \
                d["block"]["findings"] or None, d["block"]["why_it_matters"] or None

        core3_ok = core3_bad = 0
        for d in arts:
            wa, ho, fi, _wh = blocks(d)
            if wa and ho and fi:
                if max(wa) < min(ho) and max(ho) < min(fi):
                    core3_ok += 1
                else:
                    core3_bad += 1
        all4_ok = all4_bad = why_after_findings = 0
        for d in arts:
            wa, ho, fi, wh = blocks(d)
            if wa and ho and fi and wh:
                if max(wa) < min(ho) and max(ho) < min(fi):
                    all4_ok += 1
                else:
                    all4_bad += 1
                if d["first_sentence"]["findings"] is not None \
                        and min(wh) > d["first_sentence"]["findings"]:
                    why_after_findings += 1
        return {
            "pairwise_first_occurrence": pairs,
            "block_order_core3_subset": {"ok": core3_ok, "violated": core3_bad,
                                         "n": core3_ok + core3_bad},
            "block_order_all4_subset": {
                "ok": all4_ok, "violated": all4_bad, "n": all4_ok + all4_bad,
                "why_first_after_findings_first": why_after_findings},
            "n_articles_with_core_uncertainty": sum(
                1 for d in arts if d["has_core_uncertainty"]),
            "note": "'<' 严格、'=' 共现；tie 不当严格顺序；why 缺失不算违规。"
                    "含核心功能 uncertain 片段的文章另列，结论基于已确认标签。",
        }

    order = {"narrow": order_block("what"), "inclusive": order_block("what_inclusive")}

    # §10.9 框架外内容
    n_other_articles = sum(1 for d in arts if d["other_sents"])
    desc_words: Counter = Counter()
    for d in arts:
        for desc in d["other_descriptions"]:
            desc_words.update(w.lower() for w in word_count_v1(desc)[1])
    framework_out = {
        "articles_with_other": n_other_articles,
        "articles_share": round(n_other_articles / n, 4) if n else None,
        "sentences_with_other": sum(len(d["other_sents"]) for d in arts),
        "other_text_share_mean": (text_share.get("mean_share") or {}).get("other")
        if not text_share.get("disabled") else None,
        "description_word_freq_top30": desc_words.most_common(30),
        "articles_with_uncertain": sum(1 for d in arts if d["uncertain_sents"]),
        "note": "uncertain 与格式残余不计作确定新功能。",
    }

    return {
        "n_sample": len(sample_ids),
        "n_annotated": n,
        "n_annotated_in_sample": n_in_sample,
        "n_annotated_out_of_sample": n - n_in_sample,
        "n_missing_annotation": len(missing),
        "missing_annotation_article_ids": missing,
        "scope_note": "语义指标基于该来源全部已标注文章；"
                      "样本内/外篇数见 n_annotated_in/out_of_sample。"
                      "样本内未标注（模型失败）记缺失值 null。",
        "presence": presence,
        "coverage": coverage,
        "sentence_counts": sentence_counts,
        "text_share": text_share,
        "order": order,
        "framework_out": framework_out,
    }


def per_article_output(derived: dict[str, dict], sample_entries: list[dict]) -> list[dict]:
    sample_ids = {e["article_id"] for e in sample_entries}

    def row_for(aid: str, d: dict | None, anon_id, in_sample: bool) -> dict:
        row = {"article_id": aid, "anon_id": anon_id, "in_sample": in_sample}
        if d is None:
            # §10.2：模型失败 = 缺失值（null），不是 []
            row.update(function_lists=None, presence=None, coverage=None,
                       n_sents=None, primary_type=None)
        else:
            row.update(
                function_lists={**d["function_lists"],
                                "what_inclusive": d["function_lists_what_inclusive"]},
                what_inclusive_unresolved_sents=d["what_inclusive_unresolved_sents"],
                presence=d["presence"],
                coverage=d["coverage"],
                n_sents=d["n_sents"],
                first_sentence=d["first_sentence"],
                primary_type=d["primary_type"],
                text_share=d["text_share"] or None,
            )
        return row

    out = [row_for(e["article_id"], derived.get(e["article_id"]),
                   e.get("anon_id"), True) for e in sample_entries]
    for aid in sorted(set(derived) - sample_ids):
        out.append(row_for(aid, derived[aid], None, False))
    return out


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def run(corpus_path: Path, annotation_paths: list[Path], sample_path: Path | None,
        out_path: Path) -> dict:
    corpus = load_corpus(corpus_path)
    if sample_path:
        sample_entries = load_sample(sample_path)
    else:
        sample_entries = [{"article_id": r["article_id"], "anon_id": None}
                          for r in corpus.values()
                          if r["included"] and r["availability"] == "available"
                          and r.get("selected")]
    sample_ids = [e["article_id"] for e in sample_entries]

    # ---- §10.1 长度（不依赖标注）----
    recs = [corpus.get(a) for a in sample_ids]
    missing_len = [a for a, r in zip(sample_ids, recs)
                   if r is None or r.get("word_count_v1") is None]
    have = [r for r in recs if r is not None and r.get("word_count_v1") is not None]
    by_journal: dict[str, list[int]] = {}
    by_year: dict[str, list[int]] = {}
    for r in have:
        by_journal.setdefault(r["journal_code"], []).append(r["word_count_v1"])
        by_year.setdefault(str(r["year"]), []).append(r["word_count_v1"])
    length = {
        "overall": {**length_stats([r["word_count_v1"] for r in have]),
                    "n_missing_word_count": len(missing_len)},
        "by_journal": {j: length_stats(v) for j, v in sorted(by_journal.items())},
        "by_year": {y: length_stats(v) for y, v in sorted(by_year.items())},
        "note": "等额样本比例只描述该样本/等权期刊平均，不是 Top Five 篇数加权比例；"
                "2026 为 partial year。",
    }

    # ---- 各标注来源（§10.2–§10.9）----
    sources: dict = {}
    file_stats: list[dict] = []
    type_strata: dict = {}
    for ap in annotation_paths:
        name, anns, stats = load_annotations(ap)
        file_stats.append(stats)
        derived: dict[str, dict] = {}
        for aid, ann in anns.items():
            rec = corpus.get(aid)
            if rec is None or not rec.get("sentences"):
                continue
            derived[aid] = derive_article(ann, rec)
        agg = aggregate_source(derived, sample_ids)
        agg["per_article"] = per_article_output(derived, sample_entries)
        sources[name] = agg

        # §10.1 类型分层长度（标明标签来源与不确定性）
        strata: dict[str, list[int]] = {}
        for aid, d in derived.items():
            rec = corpus.get(aid)
            if rec and rec.get("word_count_v1") is not None:
                strata.setdefault(d["primary_type"] or "unknown",
                                  []).append(rec["word_count_v1"])
        type_strata[name] = {
            "label_source": stats.get("model") or stats.get("annotator") or name,
            "uncertainty": "primary_type 为摘要证据判断（模型/agent），unclear 单列；"
                           "非全文核验结论。",
            "by_primary_type": {t: length_stats(v) for t, v in sorted(strata.items())},
        }
    length["by_type"] = type_strata

    result = {
        "inputs": {
            "corpus": str(corpus_path),
            "sample": str(sample_path) if sample_path else None,
            "annotations": [str(p) for p in annotation_paths],
            "n_sample": len(sample_ids),
        },
        "length": length,
        "sources": sources,
        "model_run_stats": file_stats,
        "rules_matrix": "TODO: §10.10 规则矩阵待规则审查（第二阶段）运行后实现",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return result


def print_summary(result: dict) -> None:
    lo = result["length"]["overall"]
    print(f"样本 {result['inputs']['n_sample']} 篇；长度 n={lo.get('n')} "
          f"median={lo.get('median')} mean={lo.get('mean')} bins={lo.get('bins')} "
          f"缺词数={lo.get('n_missing_word_count')}")
    for j, s in result["length"]["by_journal"].items():
        print(f"  {j}: n={s.get('n')} median={s.get('median')} bins={s.get('bins')}")
    for name, s in result["sources"].items():
        print(f"\n== {name} ==  标注 {s['n_annotated']} 篇"
              f"（样本内 {s['n_annotated_in_sample']} / 样本外 "
              f"{s['n_annotated_out_of_sample']}；样本内缺失 {s['n_missing_annotation']}）")
        print(f"  出现状态: {s['presence']}")
        cov = s["coverage"]["narrow"]
        for k in ("core3", "why", "all4"):
            c = cov[k]
            print(f"  覆盖(narrow) {k}: 下界 {c['lower']}/{c['n']}"
                  f" 上界 {c['upper']}/{c['n']}（unresolved {c['unresolved']}）")
        for k in ("core3", "all4"):
            c = s["coverage"]["inclusive"][k]
            print(f"  覆盖(inclusive) {k}: 下界 {c['lower']}/{c['n']}"
                  f" 上界 {c['upper']}/{c['n']}")
        sc = s["sentence_counts"]["joint_what1_2_how1_findings1_2"]
        print(f"  句数联合规则: 总体 {sc['satisfied_overall']}/{sc['n_overall']}；"
              f"三功能 present 子集 {sc['satisfied_all_present']}/{sc['n_all_present']}")
        ts = s["text_share"]
        if ts.get("disabled"):
            print(f"  文本占比: 已停用（{ts['note']}）")
        else:
            print(f"  文本占比均值: {ts.get('mean_share')}"
                  f"（quote 定位失败率 {ts['quote_location']['failure_rate']}）")
        ob = s["order"]["narrow"]["block_order_core3_subset"]
        print(f"  块顺序 core3: ok {ob['ok']}/{ob['n']}（violated {ob['violated']}）"
              f"  首现对: {s['order']['narrow']['pairwise_first_occurrence']}")
        fo = s["framework_out"]
        print(f"  框架外: 文章 {fo['articles_with_other']}（{fo['articles_share']}）"
              f" 句 {fo['sentences_with_other']}")
    print("\n模型运行统计:")
    for st in result["model_run_stats"]:
        if st["format"] == "model":
            print(f"  {st['file']}: 原始成功 {st.get('n_success_original', 'NA')}"
                  f" 修复成功 {st.get('n_success_repaired', 'NA')} 失败 {st.get('n_failed', 0)}"
                  f" 费用 ¥{st.get('total_cost_cny', 'NA')}（unknown {st.get('n_cost_unknown', 0)}）"
                  f" 失败阶段 {st.get('failure_stages')}")
        else:
            print(f"  {st['file']}: agent 参照标注 {st['n_annotated']} 篇")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="摘要结构研究派生指标（设计 §10.1–§10.9）")
    ap.add_argument("--corpus", type=Path,
                    default=DEFAULT_RUN_DIR / "corpus_manifest.jsonl")
    ap.add_argument("--annotations", type=Path, nargs="+", default=None,
                    help="annotations.jsonl，可多个；默认取 run 目录下已有的模型与 agent 标注")
    ap.add_argument("--sample", type=Path,
                    default=DEFAULT_RUN_DIR / "pilot_sample_manifest.jsonl")
    ap.add_argument("--out", type=Path,
                    default=DEFAULT_RUN_DIR / "derived_metrics.json")
    args = ap.parse_args(argv)

    annotation_paths = args.annotations
    if annotation_paths is None:
        annotation_paths = []
        dev = DEFAULT_RUN_DIR / "dev_agent_annotations.jsonl"
        if dev.exists():
            annotation_paths.append(dev)
        annotation_paths.extend(sorted(DEFAULT_RUN_DIR.glob(
            "annotation_*/annotations.jsonl")))
        if not annotation_paths:
            ap.error("未找到 annotations 文件，请用 --annotations 指定")

    sample = args.sample if args.sample and args.sample.exists() else None
    result = run(args.corpus, annotation_paths, sample, args.out)
    print_summary(result)
    print(f"\n输出: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
