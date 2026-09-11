"""推文聚合统计：词数/句数分布、功能覆盖、位置×功能、功能转移矩阵。

基于 run_20260909_v03_full 全量标注（4250 篇，deepseek-v4-flash，prompt v0.3），
不新增模型调用。输出 v03_full_tweet_aggregates.json（纯派生统计，无摘要全文）。

运行：
    F:/global_venv/.venv/Scripts/python.exe build_tweet_aggregates.py
脚本内置与全量报告（notes/data/abstract_structure_full_report_v03.md）既有数字的
对账检查；不一致时列出差异并以非零码退出。
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUN_FULL = PROJECT_ROOT / "data" / "processed" / "abstract_structure" / "run_20260909_v03_full"
CORPUS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "abstract_structure" / "run_20260908_a" / "corpus_manifest.jsonl"
)
OUT_PATH = RUN_FULL / "v03_full_tweet_aggregates.json"

JOURNALS = ["AER", "JPE", "ECMA", "REStud", "QJE"]
FUNCTIONS = ["what", "how", "findings", "why_it_matters"]
SHORT = {"what": "W", "how": "H", "findings": "F", "why_it_matters": "Y"}
COLLAPSE_PRIORITY = ["findings", "how", "what", "why_it_matters"]  # F > H > W > Y
FROM_STATES = ["START", "W", "H", "F", "Y", "O"]
TO_STATES = ["W", "H", "F", "Y", "O", "END"]


# ---------------------------------------------------------------------------
# 输入加载
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def percentile(sorted_vals: list[float], p: float) -> float:
    """与 derive_metrics.length_stats 相同的线性插值分位数。"""
    n = len(sorted_vals)
    k = (n - 1) * p
    lo, hi = int(k), min(int(k) + 1, n - 1)
    return round(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo), 1)


def length_block(values: list[float]) -> dict:
    s = sorted(values)
    n = len(s)
    return {
        "n": n,
        "mean": round(sum(s) / n, 2),
        "median": percentile(s, 0.5),
        "p25": percentile(s, 0.25),
        "p75": percentile(s, 0.75),
        "p95": percentile(s, 0.95),
    }


# ---------------------------------------------------------------------------
# 对账
# ---------------------------------------------------------------------------
FAILURES: list[str] = []


def check(name: str, actual: float, expected: float, tol: float = 0.2) -> None:
    if abs(actual - expected) > tol:
        FAILURES.append(f"{name}: actual={actual} expected={expected} tol={tol}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    sample = load_jsonl(RUN_FULL / "full_sample_manifest.jsonl")
    journal_of = {r["article_id"]: r["journal_code"] for r in sample}
    year_of = {r["article_id"]: r["year"] for r in sample}
    sample_ids = set(journal_of)
    assert len(sample_ids) == 4250, len(sample_ids)

    corpus_wc = {}
    with open(CORPUS_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["article_id"] in sample_ids:
                corpus_wc[r["article_id"]] = r["word_count_v1"]
    missing_wc = sample_ids - set(corpus_wc)
    assert not missing_wc, f"语料缺 word_count_v1: {len(missing_wc)} 篇"
    assert all(v is not None for v in corpus_wc.values())

    derived = json.load(open(RUN_FULL / "v03_full_derived_deepseek-v4-flash.json", encoding="utf-8"))
    src = derived["sources"]["model:deepseek-v4-flash"]
    per_article = {a["article_id"]: a for a in src["per_article"]}

    positional = json.load(open(RUN_FULL / "v03_full_positional_deepseek-v4-flash.json", encoding="utf-8"))

    # --- 词数分布 ---
    def word_block(ids: list[str]) -> dict:
        vals = [corpus_wc[i] for i in ids]
        b = length_block(vals)
        b["pct_le100"] = round(100 * sum(v <= 100 for v in vals) / len(vals), 1)
        b["pct_101_150"] = round(100 * sum(100 < v <= 150 for v in vals) / len(vals), 1)
        b["pct_gt150"] = round(100 * sum(v > 150 for v in vals) / len(vals), 1)
        return b

    ids_by_journal = {j: [i for i in sample_ids if journal_of[i] == j] for j in JOURNALS}
    word_overall = word_block(sorted(sample_ids))
    edges = list(range(0, 321, 20)) + [10**9]
    hist = [0] * (len(edges) - 1)
    for v in corpus_wc.values():
        for k in range(len(hist)):
            if edges[k] <= v < edges[k + 1]:
                hist[k] += 1
                break
    word_hist = {
        "bin_edges": ["%d-%d" % (edges[k], edges[k + 1] - 1) if edges[k + 1] < 10**9 else "300+"
                      for k in range(len(hist))],
        "counts": hist,
    }
    word_by_journal = {j: word_block(ids_by_journal[j]) for j in JOURNALS}

    check("word.median", word_overall["median"], 106.0)
    check("word.mean", word_overall["mean"], 124.4)
    check("word.p25", word_overall["p25"], 99.0)
    check("word.p75", word_overall["p75"], 146.0)
    check("word.p95", word_overall["p95"], 203.5)
    check("word.pct_le100", word_overall["pct_le100"], 36.6)
    check("word.pct_gt150", word_overall["pct_gt150"], 21.5)
    for j, med, gt150 in [("AER", 100.0, 2.9), ("JPE", 100.0, 0.4), ("ECMA", 136.0, 30.3),
                          ("REStud", 140.5, 36.3), ("QJE", 160.0, 59.4)]:
        check(f"word.{j}.median", word_by_journal[j]["median"], med)
        check(f"word.{j}.pct_gt150", word_by_journal[j]["pct_gt150"], gt150)

    # --- 句数分布（标注口径，与 analyze_sentence_positions 一致）---
    # per_article 的 n_sents 是按功能的句数字典，总句数从 annotations 直接数。
    ann_sents: dict[str, list[dict]] = {}
    with open(RUN_FULL / "annotation_flash" / "annotations.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            out = rec.get("output", rec)
            aid = out["article_id"]
            if aid in sample_ids:
                ann_sents[aid] = sorted(out["sentence_annotations"], key=lambda s: s["sentence_id"])
    assert len(ann_sents) == 4250, len(ann_sents)
    n_sents = {a: len(s) for a, s in ann_sents.items()}

    def sent_block(ids: list[str]) -> dict:
        vals = [n_sents[i] for i in ids]
        dist = Counter(vals)
        b = length_block(vals)
        b["dist_pct"] = {str(k): round(100 * dist[k] / len(vals), 1) for k in sorted(dist)}
        return b

    sent_overall = sent_block(sorted(sample_ids))
    sent_by_journal = {j: sent_block(ids_by_journal[j]) for j in JOURNALS}
    check("sent.mean", sent_overall["mean"], 5.78, tol=0.01)
    check("sent.median", sent_overall["median"], 5.0, tol=0.01)
    check("sent.dist.4", sent_overall["dist_pct"]["4"], 19.0)
    check("sent.dist.5", sent_overall["dist_pct"]["5"], 26.1)
    check("sent.dist.6", sent_overall["dist_pct"]["6"], 20.4)
    check("sent.dist.4to6",
          sent_overall["dist_pct"]["4"] + sent_overall["dist_pct"]["5"] + sent_overall["dist_pct"]["6"],
          65.5)
    for j, mean in [("JPE", 4.89), ("AER", 5.12), ("ECMA", 6.21), ("REStud", 6.29), ("QJE", 7.21)]:
        check(f"sent.{j}.mean", sent_by_journal[j]["mean"], mean, tol=0.01)

    # --- 功能覆盖（直接采用 derived 口径；按期刊/类型从 per_article 聚合）---
    n = len(sample_ids)
    presence = {
        f: round(100 * src["presence"][f]["present"] / n, 1) for f in FUNCTIONS
    }
    presence["what_inclusive"] = round(100 * src["presence"]["what_inclusive"]["present"] / n, 1)
    coverage = {
        "core3_narrow": round(100 * src["coverage"]["narrow"]["core3"]["lower"] / n, 1),
        "core3_inclusive": round(100 * src["coverage"]["inclusive"]["core3"]["lower"] / n, 1),
        "all4_narrow": round(100 * src["coverage"]["narrow"]["all4"]["lower"] / n, 1),
        "all4_inclusive": round(100 * src["coverage"]["inclusive"]["all4"]["lower"] / n, 1),
    }
    check("presence.what", presence["what"], 76.7)
    check("presence.what_inclusive", presence["what_inclusive"], 99.6)
    check("presence.how", presence["how"], 87.6)
    check("presence.findings", presence["findings"], 98.2)
    check("presence.why", presence["why_it_matters"], 25.5)
    check("coverage.core3_narrow", coverage["core3_narrow"], 66.9)
    check("coverage.core3_inclusive", coverage["core3_inclusive"], 85.9)
    check("coverage.all4_narrow", coverage["all4_narrow"], 16.0)
    check("coverage.all4_inclusive", coverage["all4_inclusive"], 21.1)

    def core3_narrow_pct(ids: list[str]) -> float:
        ok = sum(1 for i in ids if per_article[i]["coverage"]["narrow"]["core3"]["lower"])
        return round(100 * ok / len(ids), 1)

    core3_by_journal = {j: core3_narrow_pct(ids_by_journal[j]) for j in JOURNALS}
    for j, exp in [("QJE", 75.6), ("REStud", 70.8), ("ECMA", 65.8), ("AER", 63.7), ("JPE", 62.7)]:
        check(f"core3.{j}", core3_by_journal[j], exp)

    type_ids: dict[str, list[str]] = {}
    for i in sample_ids:
        type_ids.setdefault(per_article[i]["primary_type"], []).append(i)
    core3_by_type = {t: {"n": len(ids), "core3_narrow": core3_narrow_pct(ids)}
                     for t, ids in sorted(type_ids.items())}
    check("core3.theory", core3_by_type["theory"]["core3_narrow"], 55.0)
    check("core3.empirical", core3_by_type["empirical"]["core3_narrow"], 73.8)

    how_by_type = {}
    for t, ids in sorted(type_ids.items()):
        how_by_type[t] = round(100 * sum(per_article[i]["presence"]["how"] == "present" for i in ids) / len(ids), 1)
    check("how.theory", how_by_type["theory"], 78.2)
    check("how.empirical", how_by_type["empirical"], 90.5)

    text_share = {k: round(100 * v, 1) for k, v in src["text_share"]["mean_share"].items()}
    check("share.findings", text_share["findings"], 49.4)
    check("share.how", text_share["how"], 21.4)
    check("share.what", text_share["what"], 12.5)
    check("share.why", text_share["why_it_matters"], 4.0)
    check("share.core_union", text_share["core_union"], 85.8)

    # --- 功能转移矩阵（基于 annotations 逐句标签）---
    def label_set(sent: dict) -> set[str]:
        return {f["label"] for f in sent["functions"]}

    def collapse(labels: set[str]) -> str:
        for f in COLLAPSE_PRIORITY:
            if f in labels:
                return SHORT[f]
        return "O"

    trans_counts = {a: {b: 0 for b in TO_STATES} for a in FROM_STATES}
    contains_counts = {f: {g: 0 for g in FUNCTIONS} for f in FUNCTIONS}
    contains_row_n = Counter()
    path_counter: Counter[str] = Counter()
    path_counter_by_len: dict[int, Counter[str]] = {}
    n_articles_seen = 0

    for aid, sents in ann_sents.items():
        n_articles_seen += 1
        labels = [label_set(s) for s in sents]
        chain = ["START"] + [collapse(l) for l in labels] + ["END"]
        for a, b in zip(chain, chain[1:]):
            trans_counts[a][b] += 1
        for l_cur, l_nxt in zip(labels, labels[1:]):
            for f_ in l_cur:
                contains_row_n[f_] += 1
                for g in l_nxt:
                    contains_counts[f_][g] += 1
        path = "-".join(chain)
        path_counter[path] += 1
        path_counter_by_len.setdefault(len(labels), Counter())[path] += 1
    assert n_articles_seen == 4250, n_articles_seen

    def row_pct(counts: dict[str, dict[str, int]], rows: list[str], cols: list[str]) -> dict:
        out = {}
        for a in rows:
            total = sum(counts[a].values())
            out[a] = {b: round(100 * counts[a][b] / total, 1) if total else None for b in cols}
        return out

    trans_pct = row_pct(trans_counts, FROM_STATES, TO_STATES)
    contains_pct = {
        f: {g: round(100 * contains_counts[f][g] / contains_row_n[f], 1) for g in FUNCTIONS}
        for f in FUNCTIONS
    }

    def top_paths(counter: Counter[str], k: int, denom: int) -> list[dict]:
        return [{"path": p, "n": c, "pct": round(100 * c / denom, 1)}
                for p, c in counter.most_common(k)]

    transitions = {
        "collapsed": {
            "priority_rule": "F > H > W > Y；无功能句（含 connective_only）归为 O（背景/其他）",
            "from_states": FROM_STATES,
            "to_states": TO_STATES,
            "counts": trans_counts,
            "row_pct": trans_pct,
        },
        "contains": {
            "note": "多标签句同时计入各功能；P(下一句含 g | 当前句含 f)，仅句间（不含 START/END）",
            "row_n": dict(contains_row_n),
            "counts": contains_counts,
            "row_pct": contains_pct,
        },
        "top_paths_overall": top_paths(path_counter, 10, n_articles_seen),
        "top_paths_by_sentence_count": {
            str(k): {"n_articles": sum(c.values()), "top": top_paths(c, 5, sum(c.values()))}
            for k, c in sorted(path_counter_by_len.items()) if k in (4, 5, 6)
        },
    }

    # --- 汇总输出 ---
    result = {
        "meta": {
            "generated_by": "modules/academic_research/abstract_structure/build_tweet_aggregates.py",
            "sample": "run_20260909_v03_full/full_sample_manifest.jsonl（4250 篇，五刊 2015–2026 全量合规语料）",
            "annotation_model": "deepseek-v4-flash（prompt v0.3，temperature=0）",
            "journals": JOURNALS,
            "encoding_note": positional["encoding_note"],
            "n_articles": n,
        },
        "word_count": {"overall": word_overall, "hist": word_hist, "by_journal": word_by_journal},
        "sentence_count": {"overall": sent_overall, "by_journal": sent_by_journal},
        "function_coverage": {
            "presence_pct": presence,
            "coverage_pct": coverage,
            "core3_narrow_by_journal": core3_by_journal,
            "by_type": {t: {**core3_by_type[t], "how_present": how_by_type[t]} for t in core3_by_type},
            "note": "narrow = 句子主标签口径；inclusive 含次要标签。数字与全量报告 §3 一致。",
        },
        "text_share_pct": text_share,
        "position_function": {
            "source": "v03_full_positional_deepseek-v4-flash.json",
            "matrix_all": positional["position_matrix_all"],
            "conditional": positional["conditional_on_total_sentences"],
        },
        "endpoints": positional["endpoints"],
        "transitions": transitions,
    }

    if FAILURES:
        print("对账失败：")
        for f_ in FAILURES:
            print("  -", f_)
        return 1

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"对账全部通过；已写出 {OUT_PATH}")
    print(f"词数 median={word_overall['median']} 句数 mean={sent_overall['mean']} "
          f"core3={coverage['core3_narrow']}% why={presence['why_it_matters']}%")
    print("Top3 路径:", [p["path"] for p in transitions["top_paths_overall"][:3]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
