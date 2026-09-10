"""句数分布与句子位置×功能分析：回答「一篇摘要几句」「第 i 句通常承担什么功能」。

输入：
- annotations.jsonl（run_annotation 落盘的模型格式）
- sample manifest（含 journal_code / year）

输出：positional_analysis.json + 控制台摘要。

口径：
- 句子的功能按标注的 label 集合处理（prompt 规定 functions 无序、不强制单一主功能），
  位置矩阵报告「该句标签集合包含某功能」的比例，多标签句同时计入多个功能。
- 位置模式用紧凑编码：W=what H=how F=findings Y=why_it_matters，按 W/H/F/Y 顺序拼接；
  无功能句记 O（有 other_content）/ U（仅 uncertain）/ C（connective_only）/ -（全空）。
- 只做描述，不引入新口径判断；词数相关指标不在本脚本范围。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from derive_metrics import load_annotations  # noqa: E402
from extract_abstracts import OUTPUT_ROOT  # noqa: E402

FUNCTIONS = ("what", "how", "findings", "why_it_matters")
CODE = {"what": "W", "how": "H", "findings": "F", "why_it_matters": "Y"}

DEFAULT_RUN_DIR = OUTPUT_ROOT / "run_20260909_v03_full"


def sentence_code(sa: dict) -> str:
    """单句紧凑编码：功能字母拼接；无功能时区分 O/U/C/-。"""
    labels = sorted({f.get("label") for f in sa.get("functions", [])
                     if f.get("label") in FUNCTIONS},
                    key=lambda l: FUNCTIONS.index(l))
    if labels:
        return "".join(CODE[l] for l in labels)
    if sa.get("other_content"):
        return "O"
    if sa.get("uncertain_content"):
        return "U"
    if sa.get("connective_only"):
        return "C"
    return "-"


def sentence_label_set(sa: dict) -> set[str]:
    return {f.get("label") for f in sa.get("functions", [])
            if f.get("label") in FUNCTIONS}


def percentile(sorted_vals: list[int], p: float) -> float:
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    k = (n - 1) * p
    lo, hi = int(k), min(int(k) + 1, n - 1)
    return round(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo), 1)


def count_stats(values: list[int]) -> dict:
    if not values:
        return {"n": 0}
    s = sorted(values)
    dist = Counter(s)
    return {
        "n": len(s),
        "mean": round(statistics.mean(s), 2),
        "median": statistics.median(s),
        "p5": percentile(s, 0.05), "p25": percentile(s, 0.25),
        "p75": percentile(s, 0.75), "p95": percentile(s, 0.95),
        "min": s[0], "max": s[-1],
        "distribution": {str(k): v for k, v in sorted(dist.items())},
    }


def position_matrix(rows: list[list[dict]], max_pos: int | None = None) -> list[dict]:
    """位置×功能矩阵。rows = 每篇文章的 sentence_annotations 列表。

    返回每个位置一行：落位数、各功能出现率、多标签率、other/uncertain/connective 率。
    """
    if max_pos is None:
        max_pos = max((len(r) for r in rows), default=0)
    out = []
    for pos in range(1, max_pos + 1):
        here = [r[pos - 1] for r in rows if len(r) >= pos]
        n = len(here)
        if n == 0:
            continue
        label_sets = [sentence_label_set(sa) for sa in here]
        row = {
            "position": pos,
            "n_articles_reaching": n,
            "share_reaching": None,  # 由调用方按总篇数填
            "pct_with_function": {
                f: round(sum(1 for ls in label_sets if f in ls) / n * 100, 1)
                for f in FUNCTIONS
            },
            "pct_multi_label": round(
                sum(1 for ls in label_sets if len(ls) > 1) / n * 100, 1),
            "pct_no_function": round(
                sum(1 for ls in label_sets if not ls) / n * 100, 1),
            "pct_other_content": round(
                sum(1 for sa in here if sa.get("other_content")) / n * 100, 1),
            "pct_connective_only": round(
                sum(1 for sa in here if sa.get("connective_only")) / n * 100, 1),
            "top_label_sets": [
                {"set": code, "pct": round(c / n * 100, 1)}
                for code, c in Counter(
                    "".join(CODE[l] for l in sorted(
                        ls, key=lambda x: FUNCTIONS.index(x))) or "none"
                    for ls in label_sets).most_common(6)
            ],
        }
        out.append(row)
    return out


def sequence_patterns(articles: dict[str, list[str]], top: int = 10) -> list[dict]:
    """功能编码序列模式：完整序列 -> 篇数/占比。"""
    n = len(articles)
    c = Counter(" ".join(codes) for codes in articles.values())
    return [{"pattern": pat, "n": cnt, "pct": round(cnt / n * 100, 1)}
            for pat, cnt in c.most_common(top)]


def run(annotations_path: Path, manifest_path: Path, out_path: Path,
        conditional_ns: tuple[int, ...] = (4, 5, 6)) -> dict:
    name, anns, stats = load_annotations(annotations_path)
    journal: dict[str, str] = {}
    year: dict[str, int] = {}
    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                journal[rec["article_id"]] = rec["journal_code"]
                year[rec["article_id"]] = rec["year"]

    # 每篇：句数、编码序列、按句标注列表
    n_sents: dict[str, int] = {}
    codes: dict[str, list[str]] = {}
    rows: dict[str, list[dict]] = {}
    for aid, ann in anns.items():
        sa = ann["sentence_annotations"]
        n_sents[aid] = len(sa)
        codes[aid] = [sentence_code(s) for s in sa]
        rows[aid] = sa

    total = len(anns)

    # ---- A. 总句数分布 ----
    by_journal_counts: dict[str, list[int]] = defaultdict(list)
    by_year_counts: dict[str, list[int]] = defaultdict(list)
    for aid, k in n_sents.items():
        by_journal_counts[journal.get(aid, "?")].append(k)
        by_year_counts[str(year.get(aid, "?"))].append(k)
    sentence_totals = {
        "overall": count_stats(list(n_sents.values())),
        "by_journal": {j: count_stats(v) for j, v in sorted(by_journal_counts.items())},
        "by_year": {y: count_stats(v) for y, v in sorted(by_year_counts.items())},
        "note": "句数来自标注记录覆盖的句子；2026 为 partial year。",
    }

    # ---- B. 无条件位置×功能矩阵 ----
    mat = position_matrix(list(rows.values()))
    for row in mat:
        row["share_reaching"] = round(row["n_articles_reaching"] / total * 100, 1)

    # ---- C. 按总句数条件的位置×功能矩阵 + 序列模式 ----
    conditional: dict[str, dict] = {}
    for n_target in conditional_ns:
        ids = [a for a, k in n_sents.items() if k == n_target]
        sub_rows = [rows[a] for a in ids]
        sub_mat = position_matrix(sub_rows, max_pos=n_target)
        for row in sub_mat:
            row["share_reaching"] = 100.0
        conditional[str(n_target)] = {
            "n_articles": len(ids),
            "share_of_all": round(len(ids) / total * 100, 1),
            "position_matrix": sub_mat,
            "top_patterns": sequence_patterns({a: codes[a] for a in ids}),
        }

    # ---- D. 首句 / 末句专项（含按期刊）----
    def endpoint_summary(selector) -> dict:
        sets = [selector(r) for r in rows.values()]
        n = len(sets)
        dist = Counter(
            "".join(CODE[l] for l in sorted(ls, key=lambda x: FUNCTIONS.index(x)))
            or ("O" if sa.get("other_content") else
                "C" if sa.get("connective_only") else "-")
            for sa, ls in sets)
        per_journal: dict[str, Counter] = defaultdict(Counter)
        for aid, (sa, ls) in zip(rows.keys(), sets):
            code = "".join(CODE[l] for l in sorted(
                ls, key=lambda x: FUNCTIONS.index(x))) or (
                "O" if sa.get("other_content") else
                "C" if sa.get("connective_only") else "-")
            per_journal[journal.get(aid, "?")][code] += 1
        return {
            "n": n,
            "label_set_distribution": [
                {"set": k, "n": v, "pct": round(v / n * 100, 1)}
                for k, v in dist.most_common(12)],
            "pct_with_function": {
                f: round(sum(1 for _, ls in sets if f in ls) / n * 100, 1)
                for f in FUNCTIONS},
            "by_journal_top": {
                j: [{"set": k, "pct": round(v / sum(c.values()) * 100, 1)}
                    for k, v in c.most_common(4)]
                for j, c in sorted(per_journal.items())},
        }

    endpoints = {
        "first_sentence": endpoint_summary(lambda r: (r[0], sentence_label_set(r[0]))),
        "last_sentence": endpoint_summary(lambda r: (r[-1], sentence_label_set(r[-1]))),
    }

    result = {
        "inputs": {"annotations": str(annotations_path),
                   "manifest": str(manifest_path), "source": name},
        "n_articles": total,
        "sentence_totals": sentence_totals,
        "position_matrix_all": mat,
        "conditional_on_total_sentences": conditional,
        "endpoints": endpoints,
        "encoding_note": CODE | {"O": "无功能但有 other_content",
                                 "U": "仅 uncertain", "C": "connective_only",
                                 "-": "全空"},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return result


def print_summary(result: dict) -> None:
    st = result["sentence_totals"]["overall"]
    print(f"篇数 {result['n_articles']}")
    print(f"\n== 总句数 == mean={st['mean']} median={st['median']} "
          f"p25={st['p25']} p75={st['p75']} p95={st['p95']} "
          f"范围 {st['min']}–{st['max']}")
    print("  分布:", st["distribution"])
    print("  按期刊:")
    for j, s in result["sentence_totals"]["by_journal"].items():
        d = s["distribution"]
        top = ", ".join(f"{k}句:{v}" for k, v in
                        sorted(d.items(), key=lambda kv: -kv[1])[:4])
        print(f"    {j}: n={s['n']} median={s['median']} mean={s['mean']}  {top}")

    print("\n== 位置×功能（全部文章；% = 到达该位置的句子中标签集合含该功能）==")
    header = f"{'pos':>3} {'n':>5} {'reach%':>6} | {'W':>5} {'H':>5} {'F':>5} {'Y':>5} | multi nofunc other conn | top label-sets"
    print(header)
    for row in result["position_matrix_all"][:12]:
        pf = row["pct_with_function"]
        tops = " ".join(f"{t['set']}:{t['pct']}" for t in row["top_label_sets"][:4])
        print(f"{row['position']:>3} {row['n_articles_reaching']:>5} "
              f"{row['share_reaching']:>6} | {pf['what']:>5} {pf['how']:>5} "
              f"{pf['findings']:>5} {pf['why_it_matters']:>5} | "
              f"{row['pct_multi_label']:>4} {row['pct_no_function']:>5} "
              f"{row['pct_other_content']:>4} {row['pct_connective_only']:>4} | {tops}")

    for n_str, blk in result["conditional_on_total_sentences"].items():
        print(f"\n== 总句数={n_str} 的文章（n={blk['n_articles']}，"
              f"占 {blk['share_of_all']}%）位置×功能 ==")
        for row in blk["position_matrix"]:
            pf = row["pct_with_function"]
            tops = " ".join(f"{t['set']}:{t['pct']}" for t in row["top_label_sets"][:4])
            print(f"  pos{row['position']}: W={pf['what']:>5} H={pf['how']:>5} "
                  f"F={pf['findings']:>5} Y={pf['why_it_matters']:>5} "
                  f"other={row['pct_other_content']:>4} | {tops}")
        print("  高频序列模式:")
        for p in blk["top_patterns"][:8]:
            print(f"    {p['pct']:>5}%  {p['pattern']}  (n={p['n']})")

    for ep in ("first_sentence", "last_sentence"):
        e = result["endpoints"][ep]
        print(f"\n== {ep} == 含功能: {e['pct_with_function']}")
        print("  标签集合:", " ".join(
            f"{d['set']}:{d['pct']}%" for d in e["label_set_distribution"][:8]))
        print("  按期刊 top:", {j: v[:2] for j, v in e["by_journal_top"].items()})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="句数分布与位置×功能分析")
    ap.add_argument("--annotations", type=Path,
                    default=DEFAULT_RUN_DIR / "annotation_flash" / "annotations.jsonl")
    ap.add_argument("--manifest", type=Path,
                    default=DEFAULT_RUN_DIR / "full_sample_manifest.jsonl")
    ap.add_argument("--out", type=Path,
                    default=DEFAULT_RUN_DIR / "v03_full_positional_deepseek-v4-flash.json")
    ap.add_argument("--conditional-ns", type=int, nargs="+", default=[4, 5, 6])
    args = ap.parse_args(argv)
    result = run(args.annotations, args.manifest, args.out,
                 tuple(args.conditional_ns))
    print_summary(result)
    print(f"\n输出: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
