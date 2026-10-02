"""run_table_notes.py — 用 deepseek-v4-flash 标注 top5 实证论文的表注。

每篇论文一次调用，输入该篇全部表 {序号, caption, body_head(行标签/列头), footnote}，
输出每张表注的 roles/长度/跨表指针，以及整篇的表间复用策略。

用法：
    # dry run：先看 payload 大小与 prompt，不花钱
    python modules/academic_writing/run_table_notes.py --limit 3 --dry-run
    # pilot 50
    python modules/academic_writing/run_table_notes.py --limit 50
    # 全量 748
    python modules/academic_writing/run_table_notes.py

输入：outputs/table_notes/table_units.jsonl（extract_table_units.py 产物）
输出：outputs/table_notes/run_<ts>/annotations.jsonl + failures.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB_ROOT = HERE.parents[1]
sys.path.insert(0, str(LAB_ROOT / "modules" / "academic_research" / "abstract_structure"))
from llm_client import BudgetGuard, DeepSeekClient, LLMCallError  # noqa: E402

DEFAULT_UNITS = HERE / "outputs" / "table_notes" / "table_units.jsonl"
PROMPT_VERSION = "table_notes_v0.4"

ROLES = [
    "sig_marker",      # 标准误/星号/聚类层级 (SE in parentheses, clustered at X, *p<.05)
    "table_purpose",   # 这张表在估计/报告什么 (The table presents OLS coefficients...)
    "identification",  # 识别策略 (IV, DID, RDD, RCT, instrument, fixed effects)
    "var_def",         # 变量/缩写定义或构造 (X is coded as / refers to / constructed by)
    "data_source",     # 数据来源/wave/样本期 (from X survey / See Data Appendix / 1990 Census)
    "method",          # 估计方法细节 (OLS, MLE, block bootstrap, GLS)
    "sample",          # 样本构成/限制 (control sample only / N= / excludes / balanced panel)
    "col_nav",         # 列或 panel 导航 (Column 1 is baseline / Panel A reports)
    "multiple_test",   # 多重假设校正 (FDR q-value, Romano-Wolf, family-wise)
    "cross_ref",       # 指向其他表注 (See notes to Table X / as in Table)
    "abbrev_expand",   # 把缩写展开成全称 (MTO stands for Moving to Opportunity)
    "other",
]

TABLE_TYPES = [
    "summary_stats",   # 描述样本：均值/分布/相关，无估计无检验
    "balance",         # 组间可比性检验（处理vs对照的可观测差异）
    "main_results",    # 论文核心估计/主结果
    "first_stage",     # 整表专门做 IV 第一阶段/工具变量相关性
    "robustness",      # 同一估计量换样本/设定/度量/安慰剂，验证结果不变
    "heterogeneity",   # 同一设计在不同子样本分别估计
    "mechanism",       # 检验因果路径上的中介/渠道
    "other",           # 以上都不是；必须填 table_type_other
]

SYSTEM_PROMPT = """You are annotating table notes (footnotes) in empirical economics papers.

For EACH table you are given its caption (title), body_head (the table's row/column labels),
and footnote (the note text, may be empty). Annotate:

1. n_sentences: number of sentences in the footnote (0 if empty).
   Count sentence fragments (e.g. "Standard errors in parentheses.") as sentences.
   Ignore page-continuation markers like "(continued)" — they are not note content.
2. roles: which functions the footnote's sentences serve. Choose ALL that apply from:
   - sig_marker: standard errors / significance stars / clustering level (e.g. "SE in parentheses", "clustered at classroom")
   - table_purpose: what the table estimates or reports (e.g. "The table presents OLS coefficients...")
   - identification: identification strategy (IV, DID, RDD, RCT, instrument, fixed effects)
   - var_def: variable/abbreviation definition or construction (e.g. "X is coded as...", "refers to")
   - data_source: data source / survey wave / sample period (e.g. "from the 1990 Census", "See Data Appendix")
   - method: estimation method detail (OLS, MLE, block bootstrap, GLS)
   - sample: sample composition or restriction (e.g. "control sample only", "N=", "excludes")
   - col_nav: column or panel navigation (e.g. "Column 1 is the baseline", "Panel A reports")
   - multiple_test: multiple-hypothesis correction (FDR q-value, Romano-Wolf)
   - cross_ref: pointer to another table's note (e.g. "See notes to Table 1", "as in Table")
   - abbrev_expand: expands an abbreviation into its full form (e.g. "MTO stands for Moving to Opportunity");
     use var_def instead when the note defines what a variable means or how it is constructed
   - other: none of the above
3. cross_ref_target: if cross_ref, the idx (as given in this payload) of the table it points to;
   null if there is no cross_ref, or the target is not among the tables given here.
4. abbreviated_vars: list any abbreviated variable names the footnote defines (e.g. "MTO", "ETI").
5. table_type: what this table is FOR. Choose exactly one:
   - summary_stats: descriptive statistics of the sample/variables (means, SDs, distributions);
     no estimation, no hypothesis test
   - balance: tests whether groups (e.g. treatment vs control) differ in predetermined covariates;
     rows are covariates, typically with a difference/p-value column
   - main_results: the paper's primary estimating equation(s) and headline findings
   - first_stage: the whole table is devoted to an IV first stage / instrument relevance check;
     if first stage and main IV estimates share one table, use main_results instead
   - robustness: re-estimates the SAME estimand under alternative samples/specifications/
     measurements/placebos to check it does not change
   - heterogeneity: estimates the SAME design separately across subgroups
   - mechanism: tests variables on the causal path (mediators/channels) that explain the main result
   - other: none of the above (e.g. calibration targets, institutional details, data construction,
     welfare calculations)
6. table_type_other: if table_type is "other", a short phrase (3-8 words) describing what the
   table does (e.g. "model calibration targets", "descriptive trends over time"); else null.
7. note_verdict: judge whether the given footnote really is THIS table's note. The footnote was
   extracted from the PDF by heuristics (footnote_source tells you how: "inline" = properly
   tagged; "after_body_caption" / "detached_text" = recovered from a misplaced block) and may
   occasionally be wrong. Judge by content: does it refer to this table's variables, columns,
   method, or sample? One of:
   - "ok": clearly this table's note (or empty footnote — then use null instead)
   - "wrong_table": it is a table note but belongs to a different table (e.g. it defines
     variables or results that do not match this table's caption/body)
   - "not_note": it is not a table note at all (body paragraph, figure caption, references)
   - "uncertain": cannot tell

Then for the WHOLE PAPER, based ONLY on the tables whose footnote is non-empty, decide:
   note_strategy: how notes are reused across tables that share the same variables/regressions —
   - "repeat": later tables restate similar notes in full instead of pointing back
   - "pointer": most later tables reuse earlier notes through explicit pointers ("See notes to Table X")
   - "mixed": both patterns appear, each on at least 2 tables
   - "insufficient_data": fewer than 3 tables have footnotes, or the notes are too short/generic
     to tell whether they repeat. Every paper you receive has at least one table with a footnote,
     so NEVER use this label to mean "the paper has no notes".

Return ONLY a JSON object:
{"tables":[{"idx":<int>,"n_sentences":<int>,"roles":[...],"cross_ref_target":<int|null>,"abbreviated_vars":[...],"table_type":"<type>","table_type_other":<string|null>,"note_verdict":"ok|wrong_table|not_note|uncertain|null"}],
 "note_strategy":"repeat|pointer|mixed|insufficient_data"}"""


NOTE_STRATEGIES = {"repeat", "pointer", "mixed", "insufficient_data"}
NOTE_VERDICTS = {"ok", "wrong_table", "not_note", "uncertain", None}


def validate_output(paper: dict, out: dict) -> None:
    """轻量校验：枚举值合法、tables 覆盖全部 idx，不合格抛错进 failures。"""
    if out.get("note_strategy") not in NOTE_STRATEGIES:
        raise ValueError(f"bad note_strategy: {out.get('note_strategy')!r}")
    got = [t["idx"] for t in out["tables"]]
    want = [t["idx"] for t in paper["tables"]]
    if sorted(got) != sorted(want):
        raise ValueError(f"idx mismatch: got {sorted(got)} want {sorted(want)}")
    for t in out["tables"]:
        bad = set(t["roles"]) - set(ROLES)
        if bad:
            raise ValueError(f"unknown roles {bad} at idx={t['idx']}")
        if t.get("note_verdict") not in NOTE_VERDICTS:
            raise ValueError(f"bad note_verdict {t.get('note_verdict')!r} at idx={t['idx']}")
        if t.get("table_type") not in TABLE_TYPES:
            raise ValueError(f"bad table_type {t.get('table_type')!r} at idx={t['idx']}")
        if t["table_type"] == "other" and not (t.get("table_type_other") or "").strip():
            raise ValueError(f"table_type=other but empty table_type_other at idx={t['idx']}")


def build_payload(paper: dict) -> dict:
    return {
        "paper_id": paper["paper_id"],
        "journal": paper["journal"],
        "year": paper["year"],
        "tables": [
            {
                "idx": t["idx"],
                "caption": t["caption"],
                "body_head": t["body_head"],
                "footnote": t["footnote"],
                "footnote_source": t.get("footnote_source"),
            }
            for t in paper["tables"]
        ],
    }


def norm_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", default=str(DEFAULT_UNITS))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--model", default="deepseek-v4-flash")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-cost", type=float, default=None, help="CNY 预算上限")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    units_path = Path(args.units)
    papers = [json.loads(l) for l in units_path.open(encoding="utf-8") if l.strip()]
    papers = [p for p in papers if p["has_any_note"]]  # 只标有注的
    if args.limit:
        papers = papers[: args.limit]
    print(f"papers to annotate (has_any_note): {len(papers)}")

    if args.dry_run:
        for p in papers[:3]:
            pl = build_payload(p)
            s = json.dumps(pl, ensure_ascii=False)
            print(f"  {p['paper_id']}: {len(pl['tables'])} tables, payload {len(s)} chars (~{len(s)//4} tok)")
        return 0

    run_dir = Path(args.out).resolve() if args.out else (
        HERE / "outputs" / "table_notes" / f"run_{time.strftime('%Y%m%d_%H%M%S')}"
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    ann_path = run_dir / "annotations.jsonl"
    fail_path = run_dir / "failures.jsonl"

    budget = BudgetGuard(max_cost_cny=args.max_cost) if args.max_cost else BudgetGuard()
    env_path = LAB_ROOT / ".env"
    client = DeepSeekClient(model=args.model, env_path=env_path, budget=budget, cache_dir=run_dir)
    print(f"run_dir: {run_dir}  model: {args.model}")

    ann_f = ann_path.open("a", encoding="utf-8")
    fail_f = fail_path.open("a", encoding="utf-8")
    done_ids = set()
    if ann_path.exists():
        for l in ann_path.open(encoding="utf-8"):
            if l.strip():
                done_ids.add(json.loads(l)["paper_id"])

    def process(paper):
        pl = build_payload(paper)
        try:
            resp = client.chat(SYSTEM_PROMPT, pl, norm_hash(pl), PROMPT_VERSION,
                               max_tokens=65536)
            out = json.loads(resp["content"])
            validate_output(paper, out)
            return (paper["paper_id"], {
                "paper_id": paper["paper_id"], "journal": paper["journal"],
                "year": paper["year"], "n_tables": paper["n_tables"],
                "model": resp.get("model_returned", args.model),
                "cost_cny": resp.get("cost_cny"),
                "output": out}, None)
        except (LLMCallError, json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            return (paper["paper_id"], None, {
                "paper_id": paper["paper_id"], "stage": "annotate",
                "error": str(e)[:300]})

    n_ok = n_fail = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process, p): p for p in papers if p["paper_id"] not in done_ids}
        for fut in as_completed(futs):
            pid, ann, fail = fut.result()
            if ann:
                ann_f.write(json.dumps(ann, ensure_ascii=False) + "\n"); ann_f.flush(); n_ok += 1
            else:
                fail_f.write(json.dumps(fail, ensure_ascii=False) + "\n"); fail_f.flush(); n_fail += 1
            if (n_ok + n_fail) % 25 == 0:
                print(f"  {n_ok} ok / {n_fail} fail | cost ¥{budget.total_cost_cny:.3f}")
    ann_f.close(); fail_f.close()
    print(f"DONE ok={n_ok} fail={n_fail} | tokens={budget.total_tokens} cost ¥{budget.total_cost_cny:.3f}")
    print(f"-> {ann_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
