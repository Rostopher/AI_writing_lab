# analyze_table_notes.py — 干净数据（v3 units + run_v04_full）上汇总「表注怎么写」
#
# 合并自旧 analyze_table_notes.py / analyze_note_writing.py / analyze_note_types.py。
# 类型一律用 v04 LLM 标注的 table_type（other_text 命中的回填 structural_model /
# diagnostics）；不再用 caption 关键词推断。分析层分两块：
#
#   [LLM 标注层]   run_v04_full/annotations.jsonl
#     Q1 分类型配方：有注率、句数分布、roles 占比
#     Q2 roles 频次与共现、note_strategy 分布、详略分寸、abbrev
#   [启发式句法层] table_units_v3.jsonl 的 footnote 文本（规则拆句分类，非 LLM 逐句标）
#     A  注内句子顺序：首句/末句/位置分布
#     B  同篇跨表重复：SE 句逐字/模板/各写各的、指针用法
#
# 用法：
#     python analyze_table_notes.py [--ann outputs/table_notes/run_v04_full/annotations.jsonl]
#                                   [--units outputs/table_notes/table_units_v3.jsonl]
#                                   [--save-md out.md]
#
# 只统计 footnote 非空且 note_verdict ∈ {ok, uncertain} 的表（剔除 not_note / wrong_table）。

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
DEFAULT_ANN = HERE / "outputs" / "table_notes" / "run_v04_full" / "annotations.jsonl"
DEFAULT_UNITS = HERE / "outputs" / "table_notes" / "table_units_v3.jsonl"

# table_type=other 时按 other_text 回填（v04 标注层）
BACKFILL = [
    ("structural_model", re.compile(
        r"structural|calibration|counterfactual|welfare|cost-benefit|model fit|"
        r"model parameter|model comparison|simulation|simulated|policy function|"
        r"bayes factor|equilibrium", re.I)),
    ("diagnostics", re.compile(
        r"overidentification|validity test|validating|instrument-covariate|"
        r"specification (test|comparison)", re.I)),
]

TYPE_ORDER = ["summary_stats", "balance", "main_results", "first_stage",
              "robustness", "heterogeneity", "mechanism", "structural_model",
              "diagnostics", "other"]
ROLE_ORDER = ["table_purpose", "var_def", "sig_marker", "sample", "col_nav",
              "method", "identification", "data_source", "cross_ref", "abbrev_expand"]

# ---- 句法层：注内逐句规则分类（启发式，互斥，优先级从上到下）----
SENT_RULES = [
    ("se_stars", re.compile(r"standard error|significant at|\bp[- ]?value|cluster|in parentheses|in brackets|\*\s*p\s*[<≤]|confidence interval", re.I)),
    ("col_nav", re.compile(r"\bcolumns?\s*\d|\bpanel\s+[a-z]\b|\brow[s]?\s*\d", re.I)),
    ("purpose", re.compile(r"^(this|the) (table|figure|panel) (reports?|presents?|shows?|displays?|summarizes)|^table (reports?|presents?|shows?)", re.I)),
    ("var_def", re.compile(r"\bis (defined|coded|measured|constructed|computed)|\brefers? to\b|\bdenotes?\b|\bwe (define|measure|construct)|\bequal(s)? (the|to|one)\b|\bindex\b.*\b(component|construct)", re.I)),
    ("sample", re.compile(r"\bsample\b|\bobservations?\b|\bN\s*=|\brestrict(ed|ion)?\b|\bexclud|\binclud(es|ed|ing)\b.*\b(fixed effects|controls)\b", re.I)),
    ("method", re.compile(r"\bOLS\b|\bIV\b|\b2SLS\b|\bGLS\b|\bprobit\b|\blogit\b|\bbootstrap\b|\bestimated? (by|using|with)\b|\bfixed effects?\b|\bspecification\b", re.I)),
    ("data_source", re.compile(r"\bdata\b.*\b(from|source|appendix)\b|\bcensus\b|\bsurvey\b|\bsee (data |online )?appendix\b|\b19\d\d|20[012]\d\b", re.I)),
    ("cross_ref", re.compile(r"see (the )?notes? (to|of)|as in (table|figure)|described in (the )?notes", re.I)),
]


def pct(vals, p):
    s = sorted(vals)
    if not s:
        return 0
    k = (len(s) - 1) * p
    f = int(k)
    return s[f] + (s[min(f + 1, len(s) - 1)] - s[f]) * (k - f)


def describe(vals):
    if not vals:
        return "n=0"
    s = sorted(vals)
    n = len(s)
    return (f"n={n}  mean={sum(s)/n:.2f}  "
            f"p25={pct(s,.25):.0f}  med={pct(s,.5):.0f}  "
            f"p75={pct(s,.75):.0f}  p90={pct(s,.9):.0f}  max={s[-1]}")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def split_sentences(note: str) -> list[str]:
    note = clean(note)
    note = re.sub(r"^notes?\s*[:.—\-]\s*", "", note, flags=re.I)
    parts = re.split(r"(?<=[.!?])\s+|(?<=[a-z\)])\.(?=[A-Z])", note)
    return [p.strip() for p in parts if len(p.strip()) > 3]


def classify_sent(s: str) -> str:
    for tag, pat in SENT_RULES:
        if pat.search(s):
            return tag
    return "other"


def norm_sent(s: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", s)).lower()


def load_tables(ann_path: Path, units_path: Path):
    """join 标注与 units；回填类型；只返回 verdict 通过且有注的表。"""
    units = {p["paper_id"]: p for p in
             (json.loads(l) for l in units_path.open(encoding="utf-8") if l.strip())}
    anns = [json.loads(l) for l in ann_path.open(encoding="utf-8") if l.strip()]
    backfill = Counter()
    all_tables, noted = [], []
    for a in anns:
        u = units.get(a["paper_id"])
        if not u:
            continue
        un = {t["idx"]: t for t in u["tables"]}
        for t in a["output"]["tables"]:
            ty = t.get("table_type") or "other"
            if ty == "other":
                o = (t.get("table_type_other") or "").lower()
                for new_ty, pat in BACKFILL:
                    if pat.search(o):
                        ty = new_ty
                        backfill[new_ty] += 1
                        break
            ut = un.get(t["idx"], {})
            row = {
                "paper_id": a["paper_id"], "journal": a["journal"], "idx": t["idx"],
                "type": ty, "n_sent": t.get("n_sentences", 0),
                "roles": t.get("roles") or [],
                "cross_ref_target": t.get("cross_ref_target"),
                "abbreviated_vars": t.get("abbreviated_vars") or [],
                "note_strategy": a["output"].get("note_strategy"),
                "note": ut.get("footnote") or "",
                "note_verdict": t.get("note_verdict"),
                "noted": bool(ut.get("footnote", "").strip())
                         and t.get("note_verdict") not in ("not_note", "wrong_table"),
            }
            all_tables.append(row)
            if row["noted"]:
                noted.append(row)
    return anns, all_tables, noted, backfill


def main() -> None:
    ap = argparse.ArgumentParser(description="汇总表注标注：分类型配方 + 句法层顺序/复用")
    ap.add_argument("--ann", default=str(DEFAULT_ANN))
    ap.add_argument("--units", default=str(DEFAULT_UNITS))
    ap.add_argument("--save-md", default=None)
    args = ap.parse_args()

    anns, all_tables, noted, backfill = load_tables(Path(args.ann), Path(args.units))
    out = []

    def emit(s=""):
        print(s)
        out.append(s)

    emit(f"papers: {len(anns)}  tables(all): {len(all_tables)}  noted&ok: {len(noted)}")
    if backfill:
        emit(f"type 回填: {dict(backfill)}")

    # ============ LLM 标注层 ============
    emit("\n## [标注层] Q1 分类型配方")
    all_c = Counter(t["type"] for t in all_tables)
    emit("类型分布（全部表）: " + ", ".join(
        f"{ty} {all_c.get(ty,0)} ({all_c.get(ty,0)/len(all_tables)*100:.0f}%)" for ty in TYPE_ORDER))
    emit(f"\n{'type':17s} {'n':>5s} {'有注率':>6s} {'med':>4s} {'p25':>4s} {'p75':>4s}   top roles")
    for ty in TYPE_ORDER:
        all_t = [t for t in all_tables if t["type"] == ty]
        tt = [t for t in noted if t["type"] == ty]
        if not all_t:
            continue
        ns = [t["n_sent"] for t in tt]
        rc = Counter(r for t in tt for r in set(t["roles"]))
        top = ", ".join(f"{r} {c/len(tt)*100:.0f}%" for r, c in rc.most_common(6)) if tt else "-"
        emit(f"{ty:17s} {len(all_t):5d} {len(tt)/len(all_t)*100:5.0f}% "
             f"{pct(ns,.5):4.0f} {pct(ns,.25):4.0f} {pct(ns,.75):4.0f}   {top}")

    emit("\n## [标注层] Q2 句数分布（有注表）")
    emit("overall: " + describe([t["n_sent"] for t in noted]))
    by_j = defaultdict(list)
    for t in noted:
        by_j[t["journal"]].append(t["n_sent"])
    for j in sorted(by_j):
        emit(f"  {j:8s} {describe(by_j[j])}")

    emit("\n## [标注层] roles 频次（有注表）")
    role_cnt = Counter(r for t in noted for r in t["roles"])
    role_by_journal = defaultdict(Counter)
    for t in noted:
        for r in t["roles"]:
            role_by_journal[t["journal"]][r] += 1
    n_t = len(noted)
    for r, c in role_cnt.most_common():
        emit(f"  {r:18s} {c:5d}  ({c/n_t*100:.1f}%)")
    emit("\nroles × journal (%):")
    journals = sorted(role_by_journal)
    top_roles = [r for r, _ in role_cnt.most_common(12)]
    emit(f"  {'role':18s} " + " ".join(f"{j:>7s}" for j in journals))
    for r in top_roles:
        row = f"  {r:18s} "
        for j in journals:
            tot = len(by_j[j])
            row += f"{role_by_journal[j][r]/tot*100:7.1f} "
        emit(row)

    emit("\nroles 共现 top15:")
    pair = Counter()
    for t in noted:
        rs = sorted(set(t["roles"]))
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                pair[(rs[i], rs[j])] += 1
    for (a, b), c in pair.most_common(15):
        emit(f"  {a} + {b}  {c}")

    emit("\nnote_strategy 分布（按 paper）:")
    strat = Counter(a["output"].get("note_strategy") for a in anns)
    for s, c in strat.most_common():
        emit(f"  {s or 'null':12s} {c:4d} ({c/len(anns)*100:.1f}%)")

    emit("\n详略分寸：短注 vs 长注 差的 roles（有注表）")
    ns = [t["n_sent"] for t in noted]
    med, p75 = pct(ns, .5), pct(ns, .75)
    emit(f"  median={med:.0f} p75={p75:.0f}")
    short = [t for t in noted if t["n_sent"] <= med]
    long_ = [t for t in noted if t["n_sent"] >= p75]
    short_roles = Counter(r for t in short for r in t["roles"])
    long_roles = Counter(r for t in long_ for r in t["roles"])
    emit(f"  {'role':18s} {'short%':>7s} {'long%':>7s} {'Δ':>7s}")
    for r, _ in role_cnt.most_common(15):
        s_pct = short_roles[r] / len(short) * 100 if short else 0
        l_pct = long_roles[r] / len(long_) * 100 if long_ else 0
        emit(f"  {r:18s} {s_pct:7.1f} {l_pct:7.1f} {l_pct-s_pct:+7.1f}")

    n_cross = sum(1 for t in noted if t["cross_ref_target"] is not None)
    emit(f"\n跨表指针: {n_cross}/{n_t} 有注表 ({n_cross/n_t*100:.1f}%) 含 cross_ref_target")
    n_abbr = sum(1 for t in noted if t["abbreviated_vars"])
    emit(f"缩写变量: {n_abbr}/{n_t} 表 ({n_abbr/n_t*100:.1f}%) 有 abbreviated_vars")

    # ============ 启发式句法层 ============
    emit("\n## [句法层] A. 注内句子顺序（规则分类，启发式）")
    pos_counter = defaultdict(Counter)
    first_c, last_c = Counter(), Counter()
    n_ws = 0
    for t in noted:
        sents = split_sentences(t["note"])
        if not sents:
            continue
        n_ws += 1
        tags = [classify_sent(s) for s in sents]
        first_c[tags[0]] += 1
        last_c[tags[-1]] += 1
        for i, tg in enumerate(tags):
            pos = "first" if i == 0 else ("last" if i == len(tags) - 1 else "mid")
            pos_counter[tg][pos] += 1
    emit(f"首句类型 (n={n_ws}): " + ", ".join(
        f"{k} {v/n_ws*100:.0f}%" for k, v in first_c.most_common(6)))
    emit("末句类型: " + ", ".join(
        f"{k} {v/n_ws*100:.0f}%" for k, v in last_c.most_common(6)))
    emit("各类型位置分布 (first/mid/last):")
    for tg, pc in sorted(pos_counter.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(pc.values())
        emit(f"  {tg:12s} n={tot:5d}  first {pc['first']/tot*100:4.0f}%  "
             f"mid {pc['mid']/tot*100:4.0f}%  last {pc['last']/tot*100:4.0f}%")

    emit("\n## [句法层] B. 同篇跨表重复机制")
    by_paper = defaultdict(list)
    for t in noted:
        by_paper[t["paper_id"]].append(t)
    papers2 = {pid: ts for pid, ts in by_paper.items() if len(ts) >= 2}
    emit(f"有 ≥2 张有注表的论文: {len(papers2)}")

    def tok_jac(a: str, b: str) -> float:
        ta, tb = set(a.split()), set(b.split())
        return len(ta & tb) / len(ta | tb) if ta and tb else 0.0

    pair_bucket = Counter()
    papers_verb = papers_tmpl = any_sent_verb = 0
    for pid, ts in papers2.items():
        se_sents, all_norm = [], []
        for t in ts:
            raw = split_sentences(t["note"])
            se = [s for s in raw if classify_sent(s) == "se_stars"]
            if se:
                se_sents.append(clean(se[0]).lower())
            all_norm.append({norm_sent(s) for s in raw})
        if len(all_norm) >= 2 and any(
            set.intersection(all_norm[i], all_norm[j])
            for i in range(len(all_norm)) for j in range(i + 1, len(all_norm))
        ):
            any_sent_verb += 1
        if len(se_sents) < 2:
            continue
        verb = tmpl = diff = 0
        for i in range(len(se_sents)):
            for j in range(i + 1, len(se_sents)):
                sim = tok_jac(se_sents[i], se_sents[j])
                if sim >= 0.9:
                    verb += 1
                elif sim >= 0.5:
                    tmpl += 1
                else:
                    diff += 1
        pair_bucket["verbatim"] += verb
        pair_bucket["template"] += tmpl
        pair_bucket["different"] += diff
        if verb:
            papers_verb += 1
        if tmpl:
            papers_tmpl += 1
    n_se = sum(1 for ts in papers2.values()
               if sum(1 for t in ts
                      if any(classify_sent(s) == "se_stars" for s in split_sentences(t["note"]))) >= 2)
    tot_p = sum(pair_bucket.values())
    if tot_p:
        emit(f"SE 句两两对比（{tot_p} 对 / {n_se} 篇）:")
        for k in ["verbatim", "template", "different"]:
            emit(f"  {k}: {pair_bucket[k]} ({pair_bucket[k]/tot_p*100:.0f}%)")
        emit(f"SE 句逐字重复的论文: {papers_verb}/{n_se} ({papers_verb/n_se*100:.0f}%)")
        emit(f"SE 句模板微调的论文: {papers_tmpl}/{n_se} ({papers_tmpl/n_se*100:.0f}%)")
    emit(f"任意句跨表逐字重复的论文: {any_sent_verb}/{len(papers2)} "
         f"({any_sent_verb/len(papers2)*100:.0f}%)")

    emit("\n指针句样例:")
    shown = 0
    for t in noted:
        if "cross_ref" not in t["roles"]:
            continue
        for s in split_sentences(t["note"]):
            if classify_sent(s) == "cross_ref" or re.search(r"see (the )?notes?", s, re.I):
                emit(f"  [{t['journal']}] …{s[:110]}")
                shown += 1
                break
        if shown >= 6:
            break

    if args.save_md:
        Path(args.save_md).write_text("\n".join(out), encoding="utf-8")
        print(f"\n-> {args.save_md}")


if __name__ == "__main__":
    main()
