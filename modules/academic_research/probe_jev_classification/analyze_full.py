"""
analyze_full.py — 分析 Jev 全量分类结果 vs DeepSeek 标注。

读取 jev_results_full.jsonl，输出：
1. 成分层一致率（empirical / theory / structural）
2. 主类型一致率（composed / choice）
3. 混淆矩阵
4. Choice 概率分布的 calibration（高置信度区间的准确率）
5. 不一致案例列表
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
RESULTS = HERE / f"jev_results_{sys.argv[1] if len(sys.argv) > 1 else 'full'}.jsonl"
THRESHOLD = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5


def main():
    records = []
    errors = []
    seen_ok = set()  # 断点续跑后同一 article_id 可能先有 error 行后有成功行，去重保留成功
    for line in RESULTS.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if "error" in d:
            errors.append(d)
        else:
            if d["article_id"] in seen_ok:
                continue
            seen_ok.add(d["article_id"])
            records.append(d)
    # 最后还报错才计入错误数
    n_errors = len({e["article_id"] for e in errors} - seen_ok)

    n = len(records)
    print(f"共 {n} 篇有效结果，{n_errors} 篇最终错误\n")

    # ---------- 成分层 ----------
    comp_agree = Counter()
    comp_total = Counter()
    comp_confusion = Counter()
    for r in records:
        for comp in ["empirical", "theory", "structural"]:
            ds_val = r[f"ds_{comp}"]
            jev_prob = r[f"jev_prob_{comp}"]
            if ds_val == "unclear":
                continue
            jev_bool = "yes" if jev_prob >= THRESHOLD else "no"
            comp_total[comp] += 1
            if jev_bool == ds_val:
                comp_agree[comp] += 1
            comp_confusion[f"{comp}|{ds_val}|{jev_bool}"] += 1

    print("========== 成分层一致率 ==========")
    for comp in ["empirical", "theory", "structural"]:
        ag, tot = comp_agree[comp], comp_total[comp]
        print(f"  {comp}: {ag}/{tot} = {ag/tot*100:.1f}%")
    print("\n成分层混淆:")
    for k, v in sorted(comp_confusion.items()):
        print(f"  {k} → {v}")

    # ---------- 主类型 ----------
    agree_composed = sum(1 for r in records if r["jev_composed"] == r["ds_primary_type"])
    agree_choice = sum(1 for r in records if r["jev_choice"] == r["ds_primary_type"])

    print(f"\n========== 主类型一致率 ==========")
    print(f"  composed: {agree_composed}/{n} = {agree_composed/n*100:.1f}%")
    print(f"  choice:   {agree_choice}/{n} = {agree_choice/n*100:.1f}%")

    for label, key in [("composed", "jev_composed"), ("choice", "jev_choice")]:
        conf = Counter()
        for r in records:
            conf[f"{r['ds_primary_type']}|{r[key]}"] += 1
        print(f"\n混淆矩阵 {label} (DS|Jev → count):")
        for k, v in sorted(conf.items()):
            print(f"  {k} → {v}")

    # ---------- Choice calibration ----------
    print(f"\n========== Choice confidence calibration ==========")
    bins = defaultdict(lambda: [0, 0])  # bin -> [correct, total]
    for r in records:
        probs = r.get("jev_choice_probs", {})
        if not probs:
            continue
        max_prob = max(probs.values())
        correct = r["jev_choice"] == r["ds_primary_type"]
        if max_prob >= 0.95:
            b = ">=0.95"
        elif max_prob >= 0.9:
            b = "0.90-0.95"
        elif max_prob >= 0.8:
            b = "0.80-0.90"
        elif max_prob >= 0.7:
            b = "0.70-0.80"
        elif max_prob >= 0.5:
            b = "0.50-0.70"
        else:
            b = "<0.50"
        bins[b][1] += 1
        if correct:
            bins[b][0] += 1

    for b in [">=0.95", "0.90-0.95", "0.80-0.90", "0.70-0.80", "0.50-0.70", "<0.50"]:
        if b in bins:
            c, t = bins[b]
            print(f"  {b}: {c}/{t} = {c/t*100:.1f}%")

    # ---------- 不一致案例 ----------
    disagreements = [r for r in records if r["jev_choice"] != r["ds_primary_type"]]
    print(f"\n========== Choice 不一致案例 ({len(disagreements)} 篇) ==========")
    out_path = HERE / f"disagreements_{RESULTS.stem.replace('jev_results_', '')}.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in disagreements:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"已写入 {out_path}")

    # ---------- token usage ----------
    total_input = sum(r.get("usage", {}).get("inputTokens", 0) or 0 for r in records)
    total_output = sum(r.get("usage", {}).get("outputTokens", 0) or 0 for r in records)
    print(f"\nToken 用量: input={total_input:,} output={total_output:,} total={total_input+total_output:,}")


if __name__ == "__main__":
    main()
