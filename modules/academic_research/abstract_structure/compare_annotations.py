# 比较两套结构标注（agent 参照 vs 模型，或模型 vs 模型）。
# 指标按设计 §9：句子×功能二元标签的逐类 P/R/F1、macro F1、完整标签集合一致率；
# 附 paper_type 与 component 一致率、other/uncertain 标注率对比。
# 用法：python compare_annotations.py --ref <jsonl> --pred <jsonl> [--out <json>]
import argparse
import json
from pathlib import Path

FUNCTIONS = ["what", "how", "findings", "why_it_matters"]


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def label_sets(sentence_annotations):
    """{sentence_id: set(function labels)}；other/uncertain 另计。"""
    out = {}
    for s in sentence_annotations:
        out[s["sentence_id"]] = {
            "functions": {f["label"] for f in s.get("functions", [])},
            "other": len(s.get("other_content", [])) > 0,
            "uncertain": len(s.get("uncertain_content", [])) > 0,
        }
    return out


def compare(ref_records, pred_records):
    # 两侧都兼容 run_annotation 落盘格式（{article_id, output:{…}}）与直接输出格式
    def unwrap(r):
        return r.get("output", r)
    ref_records = [unwrap(r) for r in ref_records]
    pred_by_id = {}
    for r in pred_records:
        out = unwrap(r)
        pred_by_id[out["article_id"]] = out
    per_fn = {f: {"tp": 0, "fp": 0, "fn": 0} for f in FUNCTIONS}
    n_articles = n_exact = 0
    pt_agree = 0
    comp_agree = {c: 0 for c in ("empirical_component", "theory_component", "structural_component")}
    other = {"both": 0, "ref_only": 0, "pred_only": 0, "neither": 0}
    uncertain = {"both": 0, "ref_only": 0, "pred_only": 0, "neither": 0}
    per_article = []
    for ref in ref_records:
        aid = ref["article_id"]
        if aid not in pred_by_id:
            continue
        pred = pred_by_id[aid]
        rl, pl = label_sets(ref["sentence_annotations"]), label_sets(pred["sentence_annotations"])
        n_articles += 1
        exact = all(rl[s]["functions"] == pl.get(s, {"functions": set()})["functions"] for s in rl)
        n_exact += int(exact)
        if ref["paper_type"]["primary_type"] == pred["paper_type"]["primary_type"]:
            pt_agree += 1
        for c in comp_agree:
            if ref["paper_type"][c] == pred["paper_type"][c]:
                comp_agree[c] += 1
        art = {"article_id": aid, "exact_label_set": exact,
               "ref_type": ref["paper_type"]["primary_type"],
               "pred_type": pred["paper_type"]["primary_type"]}
        for sid, r in rl.items():
            p = pl.get(sid, {"functions": set(), "other": False, "uncertain": False})
            for fn in FUNCTIONS:
                if fn in r["functions"] and fn in p["functions"]:
                    per_fn[fn]["tp"] += 1
                elif fn in p["functions"]:
                    per_fn[fn]["fp"] += 1
                elif fn in r["functions"]:
                    per_fn[fn]["fn"] += 1
            for name, table in (("other", other), ("uncertain", uncertain)):
                if r[name] and p[name]:
                    table["both"] += 1
                elif r[name]:
                    table["ref_only"] += 1
                elif p[name]:
                    table["pred_only"] += 1
                else:
                    table["neither"] += 1
        per_article.append(art)
    metrics = {}
    f1s = []
    for fn, c in per_fn.items():
        p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else None
        r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else None
        f1 = 2 * p * r / (p + r) if p and r else (0.0 if (p is not None and r is not None) else None)
        metrics[fn] = {"tp": c["tp"], "fp": c["fp"], "fn": c["fn"],
                       "precision": p, "recall": r, "f1": f1}
        if f1 is not None:
            f1s.append(f1)
    return {
        "n_articles_compared": n_articles,
        "exact_label_set_rate": n_exact / n_articles if n_articles else None,
        "macro_f1": sum(f1s) / len(f1s) if f1s else None,
        "per_function": metrics,
        "paper_type_agreement": pt_agree / n_articles if n_articles else None,
        "component_agreement": {k: v / n_articles if n_articles else None for k, v in comp_agree.items()},
        "other_sentence_crosstab": other,
        "uncertain_sentence_crosstab": uncertain,
        "per_article": per_article,
    }


def print_summary(res, ref_name, pred_name):
    print(f"ref={ref_name} pred={pred_name} n={res['n_articles_compared']}")
    print(f"exact label-set rate: {res['exact_label_set_rate']:.2f}" if res['exact_label_set_rate'] is not None else "n/a")
    print(f"macro F1: {res['macro_f1']:.3f}" if res['macro_f1'] is not None else "n/a")
    for fn, m in res["per_function"].items():
        p = f"{m['precision']:.2f}" if m['precision'] is not None else "NA"
        r = f"{m['recall']:.2f}" if m['recall'] is not None else "NA"
        f1 = f"{m['f1']:.2f}" if m['f1'] is not None else "NA"
        print(f"  {fn:14s} P={p} R={r} F1={f1} (tp={m['tp']} fp={m['fp']} fn={m['fn']})")
    print(f"paper_type agreement: {res['paper_type_agreement']:.2f}")
    print(f"component agreement: {json.dumps(res['component_agreement'])}")
    print(f"other sentences: {res['other_sentence_crosstab']}")
    print(f"uncertain sentences: {res['uncertain_sentence_crosstab']}")
    for a in res["per_article"]:
        flag = "OK " if a["exact_label_set"] else "DIFF"
        print(f"  {flag} {a['article_id'][:44]:44s} type {a['ref_type']}->{a['pred_type']}")


def main():
    ap = argparse.ArgumentParser(description="比较两套结构标注")
    ap.add_argument("--ref", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    res = compare(load_jsonl(args.ref), load_jsonl(args.pred))
    print_summary(res, Path(args.ref).name, Path(args.pred).name)
    if args.out:
        Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
